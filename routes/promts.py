
import os
import shutil
import openai
from fastapi import HTTPException
from loader import db, model
from fastapi import File, Form, UploadFile, APIRouter
from data.config import VECTOR_STORAGE_DIR



router = APIRouter()


@router.get("/get_models")
def get_models(access_token: str):
    """
    ## Retrieves the list of models available to the authenticated user.

    ## Parameters:
    * `access_token (str)`: *The authentication token used to verify the user's identity.*

    ## Returns:
    * `dict`: *A dictionary containing the status code and the list of models.*
        - *`status (int)`: Status code indicating success.*
        - *`models (list)`: List of models available to the user.*

    ## Raises:
    * `HTTPException(status_code=401, detail="Invalid token")`: *Raised if the provided access token is invalid.*
    * `HTTPException(status_code=500, detail="Error message")`: *Raised for any other unexpected errors during the process.*

    ## How it works:
    1. *Authenticates the user using the provided `access_token`.*
    2. *If the `access_token` is invalid or the user cannot be authenticated, raises a `401 Unauthorized` exception.*
    3. *Retrieves the user's ID from the authentication data.*
    4. *Fetches the list of models associated with the user's ID from the database.*
    5. *Returns a dictionary containing the status code and the list of models.*

    ## Example:

        >>> import requests
        >>> # API URL
        >>> url = "http://api_url/models/get_models"  # Replace with actual API URL
        >>> # Request payload
        >>> payload = {
        >>>     "access_token": "valid_access_token"
        >>> }
        >>> # Sending a GET request
        >>> response = requests.get(url, params=payload)
        >>> # Checking the response
        >>> if response.status_code == 200:
        >>>     print("Models retrieved successfully:", response.json())
        >>> else:
        >>>     print("Error:", response.status_code, response.json())
        >>> # Example Successful Response
        >>> {
        >>>     "status": 200,
        >>>     "models": [
        >>>         {"model_id": 1, "name": "Model A"},
        >>>         {"model_id": 2, "name": "Model B"}
        >>>     ]
        >>> }
        >>> # Example Error Response
        >>> HTTPException: {"status_code": 401, "detail": "Invalid token"}
    """
    try:
        user_data = db.login_by_token(access_token)

        if user_data is None:
            return HTTPException(status_code=401, detail="Invalid token")
        
        user_id = user_data['id']

        models = db.get_models_list(user_id)

        return {"status": 200, "models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/answer")
def get_answer(question: str, chat_id: int, access_token: str, model_name: str):
    """
    ## Retrieves an AI-generated answer based on the user's question, chat history, and the specified model.

    ## Parameters:
    * `question (str)`: *The user's question to be answered.*
    * `chat_id (int)`: *The unique identifier of the chat.*
    * `access_token (str)`: *The authentication token to verify the user's identity.*
    * `model_name (str)`: *The name of the AI model to use for generating the answer.*

    ## Returns:
    * `dict`: *A dictionary containing the status code and the AI-generated answer.*
        - *`status (int)`: HTTP status code (200 for success).*
        - *`answer (str)`: The AI-generated answer to the user's question.*

    ## Raises:
    * `HTTPException(status_code=401, detail="Invalid token")`: *Raised if the provided token is invalid.*
    * `HTTPException(status_code=404, detail="Chat not found")`: *Raised if the chat with the given `chat_id` does not exist.*
    * `HTTPException(status_code=404, detail="Model not found")`: *Raised if the specified model does not exist for the user.*
    * `HTTPException(status_code=404, detail="Limit used up")`: *Raised if the chat message limit (200) is exceeded.*
    * `HTTPException(status_code=500, detail="Error message")`: *Raised for any other unexpected server errors.*

    ## How it works:
    1. *Authenticates the user using the `access_token`.*
    2. *Verifies the existence of the chat using the `chat_id` and ensures it belongs to the authenticated user.*
    3. *If the chat name is "Unknown", updates the chat name using the first 10 characters of the question.*
    4. *Validates the existence of the specified AI model for the user.*
    5. *Associates the specified model with the chat in the database.*
    6. *Retrieves the chat history for the given chat ID, limiting to the most recent 200 messages.*
    7. *Constructs a conversation prompt using the user's question and chat history.*
    8. *Saves the user's question to the database as part of the chat history.*
    9. *Generates an AI answer using the specified model.*
    10. *Saves the AI-generated answer to the database as part of the chat history.*
    11. *Returns the AI-generated answer.*

    ## Example:

        >>> import requests
        >>> # API URL
        >>> url = "http://api_url/answer"  # Replace with actual API URL
        >>> # Request payload
        >>> payload = {
        >>>     "question": "What is AI?",
        >>>     "chat_id": 123,
        >>>     "access_token": "valid_token",
        >>>     "model_name": "gpt-4"
        >>> }
        >>> # Sending a GET request
        >>> response = requests.get(url, params=payload)
        >>> # Checking the response
        >>> if response.status_code == 200:
        >>>     print("Answer retrieved successfully:", response.json())
        >>> else:
        >>>     print("Error:", response.status_code, response.json())
        >>> # Example Successful Response
        >>> {
        >>>     "status": 200,
        >>>     "answer": "AI stands for Artificial Intelligence."
        >>> }
        >>> # Example Error Response
        >>> HTTPException: {"status_code": 401, "detail": "Invalid token"}
    """
    try:
        user_info = db.login_by_token(access_token)
        user_id = user_info['id']

        chat_info = db.get_chat_info(chat_id, user_id)
        if chat_info is None:
            return HTTPException(status_code=404, detail="Chat not found")
        
        if chat_info['name'] == "Unknown":
            db.update_chat_name(chat_id=chat_id, name=question[:10]+'...')

        model_info = db.get_model_infos(user_id=user_id, model_name=model_name)
        if model_info is None:
            return HTTPException(status_code=404, detail="Model not found"), model_info

        db.update_chat_model(chat_id=chat_id, model_id=model_info['id'])

        chat_history = db.get_chat_messages(chat_id, user_id)
        if not chat_history:
            chat_history = []
        
        if len(chat_history) > 200:
            return HTTPException(status_code=404, detail="Limit used up")

        prompts = model.create_promts(question, chat_history)
        
        db.save_chat_message(chat_id=chat_id, user_id=user_id, content=question, role='user', model_id=model_info['id'])

        answer = model.get_answer(api_key=user_info['api_key'], prompt=prompts, model_data=model_info, query=question)

        db.save_chat_message(chat_id=chat_id, user_id=user_id, content=answer, role="assistant", model_id=model_info['id'])

        return {"status": 200, "answer": answer}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get_model_info")
def get_model_info(models_name: str, access_token: str):
    """
    ## Retrieves information about a specific model for the authenticated user.

    ## Parameters:
    * `models_name (str)`: *The name of the model to retrieve information about.*
    * `access_token (str)`: *The authentication token used to verify the user's identity.*

    ## Returns:
    * `dict`: *A dictionary containing the status code and the model's information.*
        - *`status (int)`: HTTP status code (200 for success).*
        - *`model_data (dict)`: The details of the requested model, including its attributes.*

    ## Raises:
    * `HTTPException(status_code=401, detail="Invalid token")`: *Raised if the provided token is invalid.*
    * `HTTPException(status_code=404, detail="Model not found")`: *Raised if the specified model does not exist or is inaccessible for the user.*
    * `HTTPException(status_code=500, detail="Error message")`: *Raised for any unexpected server errors.*

    ## How it works:
    1. *Authenticates the user using the `access_token`.*
    2. *Retrieves the user's ID from the authentication data.*
    3. *Fetches the model information from the database using the `user_id` and `model_name`.*
    4. *If the model does not exist or is not accessible to the user, raises a `404` exception.*
    5. *Returns the model information in a structured response.*

    """
    try:
        user_data = db.login_by_token(access_token)

        if user_data is None:
            return HTTPException(status_code=401, detail="Invalid token")
        
        user_id = user_data['id']

        data = db.get_model_infos(user_id=user_id, model_name=models_name)

        if data is None:
            return HTTPException(status_code=404, detail="Model not found")

        return {"status": 200, "model_data": data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload_model/")
async def upload_file(file: UploadFile = File(...), 
                      model_name: str = Form(...), 
                      description: str = Form(...),
                      system: str = Form(...),
                      visibility: bool = Form(...),
                      max_tokens: int = Form(...),
                      access_token: str = Form(...)):
    """
    ## Uploads a PDF file and builds a RAG-based model for document retrieval and querying.

    ## Parameters:
    * `file (UploadFile)`: *The uploaded file. Must be in PDF format.*
    * `model_name (str)`: *The name of the model being created.*
    * `description (str)`: *A short description of the model's purpose or functionality.*
    * `system (str)`: *System context or configuration for the model's operations.*
    * `visibility (bool)`: *Determines whether the model is publicly visible (`True`) or private (`False`).*
    * `max_tokens (int)`: *The maximum number of tokens the model can handle.*
    * `access_token (str)`: *Authentication token to verify the user's identity.*

    ## Returns:
    * `dict`: *A dictionary containing the status code and the document ID (`doc_id`) of the uploaded model.*
        - *`status_code (int)`: HTTP status code (200 for success).*
        - *`doc_id (str)`: The unique document ID of the uploaded model.*

    ## Raises:
    * `HTTPException(status_code=400, detail="Invalid file format. Only PDF files are allowed.")`: *Raised if the uploaded file is not a PDF.*
    * `HTTPException(status_code=401, detail="Invalid token")`: *Raised if the authentication token is invalid.*
    * `HTTPException(status_code=401, detail="Model building failed in save to db")`: *Raised if the model fails to save to the database.*
    * `HTTPException(status_code=401, detail="Model building failed in embedding")`: *Raised if document embedding fails during processing.*
    * `HTTPException(status_code=401, detail="AuthenticationError")`: *Raised if an OpenAI authentication error occurs.*
    * `HTTPException(status_code=500, detail="Error message")`: *Raised for any unexpected errors during processing.*
    * `HTTPException(status_code=400, detail="Model name already exists.")`: If model name alreadey exists.

    ## How it works:
    1. *Validates that the uploaded file is in PDF format.*
    2. *Authenticates the user using the provided `access_token`.*
    3. *Saves the uploaded PDF to the server.*
    4. *Uses the `add_document` method to embed the document and generate a unique document ID (`doc_id`).*
    5. *Inserts the model details into the database using `db.insert_model`.*
    6. *If successful, returns the document ID (`doc_id`) with a status code of 200.*
    7. *Handles errors gracefully with appropriate HTTP exceptions.*
    8. If model's name already exists return `HTTPException(status_code=400, detail="Model name already exists.")`
    """
    try:
        if not file.filename.endswith(".pdf"):
            return HTTPException(status_code=400, detail="Invalid file format. Only PDF files are allowed.")

        check_model = db.check_email_exists(model_name)
        if check_model: 
            return HTTPException(status_code=400, detail="Model name already exists.")
        user_data = db.login_by_token(access_token)
        if user_data is None:
            return HTTPException(status_code=401, detail="Invalid token")
        
        save_path = f"{VECTOR_STORAGE_DIR}/{model_name}.pdf"
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        user_id = user_data['id']
        doc_id = model.add_document(pdf_path=save_path, document_name=model_name, api_key=user_data['api_key'])

        save_db = db.insert_model(name=model_name, 
                                  description=description,
                                  system=system,
                                  visibility=visibility,
                                  max_tokens=max_tokens,
                                  creator_id=user_id,
                                  model_type='rag_model',
                                  doc_id=doc_id)
        if save_db is None:
            return HTTPException(status_code=401, detail="Model building failed in save to db")

        if doc_id is not None:
            os.remove(save_path)
            return {"status_code": 200, "doc_id": doc_id}
        else:
            return HTTPException(status_code=401, detail="Model building failed in embedding")
    except openai.AuthenticationError as e:
        return HTTPException(status_code=401, detail=e.message)
    except Exception as err:
        return HTTPException(status_code=500, detail=str(err))
     

@router.delete("/delete_model")
def delete_model(model_id: str, access_token: str):
    """
    ## Deletes a specific model for the authenticated user.

    ## Parameters:
    * `model_id (str)`: *The unique identifier of the model to be deleted.*
    * `access_token (str)`: *Authentication token to verify the user's identity.*

    ## Returns:
    * `dict`: *A dictionary indicating the deletion status.*
        - *`status_code (int)`: HTTP status code (200 for success).*
        - *`message (str)`: A success message confirming deletion.*

    ## Raises:
    * `HTTPException(status_code=401, detail="Invalid token")`: *Raised if the provided authentication token is invalid.*
    * `HTTPException(status_code=404, detail="Model not found")`: *Raised if the specified model does not exist or is inaccessible to the user.*
    * `HTTPException(status_code=403, detail="Unauthorized action")`: *Raised if the user does not have permission to delete the model.*
    * `HTTPException(status_code=500, detail="Error message")`: *Raised for any other unexpected errors during processing.*

    ## How it works:
    1. *Authenticates the user using the provided `access_token`.*
    2. *Checks if the specified `model_id` exists and belongs to the authenticated user.*
    3. *Verifies the user's permission to delete the model.*
    4. *Deletes the model metadata and associated data from the database.*
    5. *Removes any related files from the server's storage.*
    6. *Returns a confirmation message upon successful deletion.*

    """
    try:
        user_data = db.login_by_token(access_token)

        if user_data is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_id = user_data['id']

        model_data = db.get_model_by_id(model_id, user_id)
        if model_data is None:
            raise HTTPException(status_code=404, detail="Model not found")

        if model_data['creator_id'] != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized action")

        db.delete_model(model_id)

        vector_path = model_data.get("vectors_path")
        if vector_path and os.path.exists(vector_path):
            shutil.rmtree(vector_path)

        return {"status_code": 200, "message": "Model deleted successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
