import os
import uuid
import json
import replicate
from data.config import VECTOR_STORAGE_DIR, METADATA_FILE, REPLECATE_API
from typing import List, Dict
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


"""
LLM Class
---------
This class provides functionalities to work with various language models (LLMs), manage document embeddings, handle document-based queries, and interact with OpenAI and other model APIs. It supports PDF processing, embedding generation, and query execution using retrieval-augmented generation (RAG) techniques.

Attributes:
    - embeddings: Manages embedding generation for documents.
    - documents_metadata: Stores metadata about documents.

"""

class LLM:

    """
    Main class to handle document embeddings, queries, and LLM-based tasks.

    Methods:
    --------
    __init__:
        Initializes the class, creates necessary directories, and loads metadata.
    
    load_metadata:
        Loads metadata of processed documents.
    
    save_metadata:
        Saves metadata of processed documents.
    
    add_document:
        Adds a PDF document, splits it into chunks, and stores embeddings.
    
    list_documents:
        Lists all added documents and their metadata.
    
    get_document_retriever:
        Retrieves a retriever object for a specific document.
    
    query_document:
        Queries a document for a given input using a specified system prompt.
    
    open_ai_chat:
        Sends a chat-based query to OpenAI and retrieves the response.
    
    get_answer:
        Executes a query using specified model information and returns an answer.
    
    create_promts:
        Builds a prompt structure for dialog-based queries.
    
    generate_llama2_response:
        Generates a response using the Llama 2 model from Replicate API.
    """


    def __init__(self):
        """
        Initializes the LLM class.

        Purpose:
        --------
        - Creates a directory for vector storage if it does not exist.
        - Initializes the `embeddings` attribute with the OpenAI embedding model.
        - Loads metadata from a file if it exists; otherwise, initializes an empty metadata dictionary.

        Parameters:
        -----------
        None

        Returns:
        --------
        None
        """
        os.makedirs(VECTOR_STORAGE_DIR, exist_ok=True)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.replicate_api = REPLECATE_API
        os.environ['REPLICATE_API_TOKEN'] = self.replicate_api
        self.load_metadata()


    def load_metadata(self):
        """
        Loads metadata of previously added documents from a JSON file.

        Purpose:
        --------
        - Checks if the `METADATA_FILE` exists.
        - If it exists, loads its content into the `documents_metadata` attribute.
        - If it does not exist, initializes `documents_metadata` as an empty dictionary.

        Parameters:
        -----------
        None

        Returns:
        --------
        None
        """

        if os.path.exists(METADATA_FILE):
            with open(METADATA_FILE, 'r') as f:
                self.documents_metadata = json.load(f)
        else:
            self.documents_metadata = {}


    def save_metadata(self):
        """
        Saves the current metadata of documents into a JSON file.

        Purpose:
        --------
        - Writes the content of the `documents_metadata` attribute into the `METADATA_FILE`.

        Parameters:
        -----------
        None

        Returns:
        --------
        None
        """

        with open(METADATA_FILE, 'w') as f:
            json.dump(self.documents_metadata, f, indent=4)


    def add_document(self, pdf_path: str, api_key: str, document_name: str = None):
        """
        Adds a new PDF document by generating embeddings and storing metadata.

        Purpose:
        --------
        - Loads the PDF document.
        - Splits the document text into smaller chunks for efficient processing.
        - Generates embeddings for the chunks using the OpenAI embedding model.
        - Saves the embeddings and metadata to the file system.

        Parameters:
        -----------
        pdf_path (str): Path to the PDF document.
        api_key (str): API key for the OpenAI embedding model.
        document_name (str, optional): Custom name for the document. Defaults to the file name if not provided.

        Returns:
        --------
        str: A unique identifier (`doc_id`) for the added document.

        Raises:
        -------
        None
        """
        if not document_name:
            document_name = os.path.basename(pdf_path)
        doc_id = str(uuid.uuid4())
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = text_splitter.split_documents(documents)
        persist_directory = os.path.join(VECTOR_STORAGE_DIR, doc_id)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small", 
                                           api_key=api_key)
        vectorstore = Chroma.from_documents(
            documents=texts,
            embedding=self.embeddings,
            persist_directory=persist_directory
        )
        self.documents_metadata[doc_id] = {
            "name": document_name,
            "path": pdf_path,
            "vectors_path": persist_directory
        }
        self.save_metadata()

        print(f"Dokument muvaffaqiyatli qo'shildi: {document_name}")
        return doc_id


    def list_documents(self) -> List[Dict]:
        """
        Lists metadata of all added documents.

        Purpose:
        --------
        - Retrieves a list of all documents stored in the system, including their metadata.

        Parameters:
        -----------
        None

        Returns:
        --------
        List[Dict]: A list of dictionaries, each containing metadata for a document.

        Raises:
        -------
        None
        """

        return list(self.documents_metadata.values())


    def get_document_retriever(self, doc_id: str, api_key: str):
        """
        Retrieves a retriever object for querying a specific document.

        Purpose:
        --------
        - Retrieves embeddings and vector storage for a given document.
        - Creates a retriever for querying the document using a similarity search.

        Parameters:
        -----------
        doc_id (str): Unique identifier for the document.
        api_key (str): API key for the OpenAI embedding model.

        Returns:
        --------
        Retriever: An object to query the document using vector-based search.

        Raises:
        -------
        ValueError: If the document ID does not exist in `documents_metadata`.
        """

        if doc_id not in self.documents_metadata:
            raise ValueError(f"Dokument ID {doc_id} topilmadi")

        persist_directory = self.documents_metadata[doc_id]['vectors_path']
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small", 
                                           api_key=api_key)
        vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings
        )

        return vectorstore.as_retriever(search_kwargs={"k": 3})


    def query_document(self, doc_id: str, query: str, api_key: str, system: str, chat_history: list, max_tokens=1000):
        """
        Queries a document for a given input using a system prompt and a retrieval-augmented generation (RAG) pipeline.

        Purpose:
        --------
        - Retrieves the document retriever for the given document ID.
        - Uses an OpenAI chat model to process the query.
        - Combines the document context and query to generate an answer.

        Parameters:
        -----------
        doc_id (str): Unique identifier for the document.
        query (str): User query or question.
        api_key (str): API key for OpenAI.
        system (str): System instructions or prompt for the query.
        chat_history (list): Chat history for context.
        max_tokens (int): Maximum number of tokens for the model's response. Default is 1000.

        Returns:
        --------
        str: The answer generated from the document and query.

        Raises:
        -------
        ValueError: If the document ID does not exist.
        Exception: For any errors during query processing.
        """
        try:
            retriever = self.get_document_retriever(doc_id, api_key=api_key)
            
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=api_key,
                temperature=0.3,
                max_tokens=max_tokens
            )


            system_prompt = (
            f"{system}\n"
            "Context: {context}")
            messages = [("system", system_prompt)]
            if chat_history:
                for history in chat_history:  
                    role = history.get("role", "")
                    if role == 'assistant':
                        role = 'ai'
                    elif role == 'user':
                        role = 'human'
                    
                    if role and 'content' in history:
                        messages.append((role, history["content"]))
            messages.append(("human", "{input}"))

            prompt = ChatPromptTemplate.from_messages(messages)

            question_answer_chain = create_stuff_documents_chain(llm, prompt)

            chain = create_retrieval_chain(retriever, question_answer_chain)
            print(prompt)


            res = chain.invoke({"input": query})
            return res['answer']

        
        except Exception as e:
            raise ValueError(f"Error processing document query: {str(e)}")


    def open_ai_chat(self,model: str, prompt: str, api_key: int, max_tokens=1000):
        """
        Interacts with OpenAI's chat models to process a given prompt.

        Purpose:
        --------
        - Sends a prompt to an OpenAI chat model and retrieves the response.

        Parameters:
        -----------
        model (str): The name of the OpenAI model to use.
        prompt (str): The input prompt or query for the model.
        api_key (str): API key for OpenAI.
        max_tokens (int, optional): Maximum number of tokens for the model's response. Default is 1000.

        Returns:
        --------
        str: The response from the OpenAI chat model.

        Raises:
        -------
        Exception: For errors during API interaction.
        """

        try:
            self.client = OpenAI(api_key=api_key,)
            response = self.client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=prompt
            )
            return response.choices[0].message.content
        except Exception as e:
            print(e)
            return f"Error: {str(e)}"
        

    def get_answer(self, prompt, api_key: str, model_data: dict, query: str):
        """
        Determines the appropriate method to process a query based on the model type.

        Purpose:
        --------
        - Handles different types of models (chat, RAG, or Llama) to generate a response.
        - Uses the corresponding method to query the model.

        Parameters:
        -----------
        prompt (str): Input prompt or query.
        api_key (str): API key for model interaction.
        model_data (dict): Dictionary containing model type and configuration details.
        query (str): The actual query to process.

        Returns:
        --------
        str: The answer generated by the model.

        Raises:
        -------
        Exception: For any errors during the query process.
        """
        try:
            if model_data['type'] == 'chat':
                return self.open_ai_chat(model_data['name'], prompt, api_key)
            elif model_data['type'] == 'rag_model':
                res = self.query_document(doc_id=model_data['doc_id'], query=query, api_key=api_key, system=model_data['system'], chat_history=prompt)
                return res
            elif model_data['type'] == 'llama':
                res = self.generate_llama2_response(query, prompt)
                return res
            else:
                return "Invalid model type"
        except Exception as err:
            print(err)
            return str(err)


    def create_promts(self, promt: str, prompt_history):
        """
        Generates a structured prompt for dialog-based queries.

        Purpose:
        --------
        - Combines previous conversation history with the current user prompt.
        - Formats the conversation into a structure compatible with OpenAI chat models.

        Parameters:
        -----------
        promt (str): The user's current prompt.
        prompt_history (list): List of previous conversation messages, with each message as a dictionary.

        Returns:
        --------
        List[Dict]: A formatted list of conversation messages.

        Raises:
        -------
        Exception: For errors during prompt creation.
        """
        try:
            promts = []
            for i in prompt_history:
                p = {"role": i["role"], "content": i["content"]}
                promts.append(p)
            promts.append({"role": "user", "content": promt})
            return promts
        except Exception as e:
            print(e)
            return f"Error: {str(e)}"
        except Exception as e:
            print(e)
            return f"Error: {str(e)}"
        

    def generate_llama2_response(self, prompt_input, chat_history: list):
        """
        Generates a response using the Llama 2 model via the Replicate API.

        Purpose:
        --------
        - Processes a dialog history and generates a response from the Llama 2 model.
        - Formats the input history and prompt to match the Llama 2 API's requirements.

        Parameters:
        -----------
        prompt_input (str): The user's current input or question.
        chat_history (list): List of previous conversation messages, with each message as a dictionary.

        Returns:
        --------
        str: The response generated by the Llama 2 model.

        Raises:
        -------
        Exception: For errors during interaction with the Replicate API.
        """


        string_dialogue = "You are a helpful assistant. You do not respond as 'User' or pretend to be 'User'. You only respond once as 'Assistant'."
        replicate.Client(api_token=self.replicate_api)
        for dict_message in chat_history:
            if dict_message["role"] == "user":
                string_dialogue += "User: " + dict_message["content"] + "\n\n"
            else:
                string_dialogue += "Assistant: " + dict_message["content"] + "\n\n"
        
        output = replicate.run('a16z-infra/llama7b-v2-chat:4f0a4744c7295c024a1de15e1a63c880d3da035fa1f49bfd344fe076074c8eea', 
                            input={"prompt": f"{string_dialogue} {prompt_input} Assistant: ",
                                    "temperature":0.5, "top_p":0.5, "max_length":200, "repetition_penalty":1})
        full_response = ''
        for item in output:
            full_response += item
        print(full_response)
        return full_response