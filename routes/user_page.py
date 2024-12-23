from fastapi import HTTPException
from loader import db
from fastapi import APIRouter


router = APIRouter()


@router.post("/get_chats")
def get_chat_list(access_token: str):
    """
    ## Retrieves the list of chats for a user.

    ## Parameters:
    * `access_token (str)`: *A string representing the user's access token.*

    ## Returns:
    * `dict`: *A dictionary containing the list of chats associated with the user.*
        - *`chats (list)`: A list of chat objects retrieved from the database.*

    ## Raises:
    * `HTTPException(status_code=404, detail="User not found")`: *Raised if the user cannot be found based on the provided access token.*
    * `HTTPException(status_code=500, detail="Error message")`: *Raised for any other unexpected errors during the process.*

    ## How it works:
    1. *Fetches the user's information using the provided `access_token`.*
    2. *If the `access_token` is invalid or the user does not exist, raises a `404` error with the message "User not found".*
    3. *Extracts the user's ID from the retrieved information.*
    4. *Fetches the list of chats associated with the user's ID from the database.*
    5. *Returns the list of chats in a dictionary format.*

    """
    try:
        user_info = db.login_by_token(access_token)

        if user_info is None:
            return HTTPException(status_code=404, detail="User not found")
        
        user_id = user_info["id"]

        chats = db.get_user_chat_list(user_id)

        return {"chats": chats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/get_chat_data")
def get_chat_data(access_token: str, chat_id: int):
    """
    ## Retrieves the details of a specific chat for the authenticated user.

    ## Parameters:
    * `access_token (str)`: *The authentication token to verify the user's identity.*
    * `chat_id (int)`: *The ID of the chat to retrieve.*

    ## Returns:
    * `dict`: *A dictionary containing the chat data, including messages.*
        - *`chat_data (list)`: A list of message objects, each containing:*
            - *`role (str)`: The role of the message sender (e.g., "user", "system").*
            - *`content (str)`: The content of the message.*
            - *`timestamp (str)`: The time the message was sent.*

    ## Raises:
    * `HTTPException(status_code=404, detail="User not found")`: *Raised if the user cannot be authenticated with the provided access token.*
    * `HTTPException(status_code=404, detail="Chat not found")`: *Raised if the chat with the given `chat_id` does not exist or does not belong to the authenticated user.*
    * `HTTPException(status_code=500, detail="Error message")`: *Raised for any other unexpected errors during the process.*

    ## How it works:
    1. *Authenticates the user using the provided `access_token`.*
    2. *If the user is not found, raises an HTTPException with a 404 status code and the message "User not found".*
    3. *Uses the authenticated user's ID and the provided `chat_id` to fetch the chat data from the database.*
    4. *If the chat does not exist or is not associated with the user, raises a 404 exception with the message "Chat not found".*
    5. *Returns the chat data, including messages, in a dictionary format.*

"""
    try:
        user_info = db.login_by_token(access_token)

        if user_info is None:
            return HTTPException(status_code=404, detail="User not found")
        
        user_id = user_info["id"]

        chat_data = db.get_chat_data(chat_id, user_id)

        return {"chat_data": chat_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create_chat")
def create_chat(access_token: str, model_id=1):
    """
    ## Creates a new chat for the authenticated user.

    ## Parameters:
    * `access_token (str)`: *The authentication token to verify the user's identity.*
    * `model_id (int, optional)`: *The ID of the model to associate with the new chat. Defaults to 1.*

    ## Returns:
    * `dict`: *A dictionary containing the ID of the newly created chat.*
        - *`chat_id (int)`: The ID of the created chat.*

    ## Raises:
    * `HTTPException(status_code=404, detail="User not found")`: *Raised if the user cannot be authenticated with the provided access token.*
    * `HTTPException(status_code=500, detail="Error message")`: *Raised for any other unexpected errors during the process.*

    ## How it works:
    1. *Authenticates the user using the provided `access_token`.*
    2. *If the `access_token` is invalid or the user does not exist, raises a `404` error with the message "User not found".*
    3. *Retrieves the authenticated user's ID from the user information.*
    4. *Creates a new chat in the database using the user's ID, a default chat name ('Unknown'), and the specified `model_id`.*
    5. *Returns the ID of the newly created chat.*

"""
    try:
        user_info = db.login_by_token(access_token)

        if user_info is None:
            return HTTPException(status_code=404, detail="User not found")
        
        user_id = user_info["id"]

        chat_id = db.create_new_chat(user_id, 'Unknown', model_id)

        return {"chat_id": chat_id}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

        
