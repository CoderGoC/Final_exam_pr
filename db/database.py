import mysql.connector
import logging
import hashlib
from typing import Dict, List

import mysql.connector.cursor


class Database:
    """
    A class to manage database interactions, including user authentication, access_token management e.t.c.

    Attributes:
        host (str): The hostname of the MySQL server.
        user (str): The username for the MySQL database.
        password (str): The password for the MySQL database.
        database (str): The name of the database to connect to.
        connection (mysql.connector.connection_cext.CMySQLConnection): Database connection object.
        cursor (mysql.connector.cursor_cext.CMySQLCursorDict): Database cursor object.

    Example:
        >>> db = Database(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE)

    """

    def __init__(self, host, user, password, database):
        """
        Initializes the database connection.

        Parameters:
            host (str): The hostname of the MySQL server.
            user (str): The username for the MySQL database.
            password (str): The password for the MySQL database.
            database (str): The name of the database to connect to.

        Example:
            >>> db = Database(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE)
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.reconnect()


    def reconnect(self):
        """
        Establishes a new connection to the database.

        Example:

            >>> db = Database(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE)
            >>> try:
            >>>     db.ensure_connection()
            >>>     sql = "SELECT * FROM users WHERE email = %s"
            >>>     db.cursor.execute(sql, (email,))
            >>>     return db.cursor.fetchone()
            >>> except mysql.connector.Error as err:
            >>>     logging.error(f"Email check error: {err}")
            >>>     db.reconnect()
            >>> finally:
            >>>     db.cursor.nextset()

        Raises:
            mysql.connector.Error: If the connection fails.
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                connection_timeout=30,
                autocommit=True
            )
            self.cursor = self.connection.cursor(dictionary=True)
        except mysql.connector.Error as err:
            logging.error(f"Database connection error: {err}")
            raise
    

    def ensure_connection(self):
        """
        Ensurance connection.
        """
        if not self.connection.is_connected():
            logging.warning("Connection lost, reconnecting...")
            self.reconnect()


    def create_user_table(self):
        """
        Creates a table for storing user information.

        Table schema:
            - id: INT (Primary key, auto-increment)
            - username: VARCHAR(50) (Unique, not null)
            - email: VARCHAR(100) (Unique, not null)
            - name: VARCHAR(100) User Name.
            - surname: VARCHAR(100) User Surname.
            - api_key: TEXT User OpenAI API KEY.
            - phone_number: VARCHAR(20) User Phone Number.
            - last_login: DATETIME User Last Login.
            - date_joined: DATETIME (Default: CURRENT_TIMESTAMP).
            - password: VARCHAR(255) (Hashed, not null)
            - token: VARCHAR(255) (Unique)
            - date: DATETIME (Default: CURRENT_TIMESTAMP)


        Raises:
            mysql.connector.Error: If the create fails.
        """
        try:
            self.ensure_connection()
            sql = """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(100),
                    surname VARCHAR(100),
                    api_key TEXT,
                    phone_number VARCHAR(20),
                    last_login DATETIME,
                    date_joined DATETIME DEFAULT CURRENT_TIMESTAMP,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    access_token VARCHAR(255) UNIQUE
                );
            """
            self.cursor.execute(sql)
        except mysql.connector.Error as err:
            logging.error(f"Create user table error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def register_user(self, username, email, password, access_token, surname, name, api_key):
        """
        Registers a new user with user data, hashing the password.

        Parameters:
            username (str): The user's username.
            email (str): The user's email.
            password (str): The user's plaintext password.
            access_token (str, optional): A unique access_token for the user. Defaults to None.
            surname (str): The user's surname.
            name (str): The user's name.
            api_key (str): The user's OpenAI key.


        Returns:
            int: The ID of the newly created user.

        Raises:
            mysql.connector.Error: If the registration fails.
        """
        try:
            self.ensure_connection()
            hashed_password = self.hash_password(password)
            sql = """
            INSERT INTO users (username, email, password, access_token, surname, name, api_key) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            values = (username, email, hashed_password, access_token, surname, name, api_key)
            self.cursor.execute(sql, values)
            return self.cursor.lastrowid
        except mysql.connector.Error as err:
            logging.error(f"User registration error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def login_user(self, username, password):
        """
        Logs in a user by verifying their credentials.

        Parameters:
            username (str): The user's username.
            password (str): The user's plaintext password.


        Returns:
            dict: User information if login is successful, otherwise None.

        Raises:
            mysql.connector.Error: If the login process fails.
        """
        try:
            self.ensure_connection()
            sql = "SELECT * FROM users WHERE username = %s"
            self.cursor.execute(sql, (username,))
            user = self.cursor.fetchone()
            if user and self.verify_password(user['password'], password):
                return user
            return None
        except mysql.connector.Error as err:
            logging.error(f"Login error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def update_user(self, user_id, email, surname, name, api_key, phone_number):
        try:
            """
            Updates a user's information in the database.
            `user_id` is identeficator for user.

            Parameters:
                user_id (int): The ID of the user to update.
                email (str): The new email for the user.
                surname (str): The new Surname for the user.
                name (str): The new Name for the user.
                api_key (str): The new OpenAi api_key for the user.
                phone_number (str): The new Phone Number for the user.
            
            Example:

                >>> db = Database(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE)
                >>> update = db.update_user(1, 'new_email@example.com', 'NewSurname', 'NewName', 'new_api_key', '+1234567890')
            Retruns:
                True: If update is successful, otherwise False.

            Raises:
                mysql.connector.Error: If the update process fails.
            """

            self.ensure_connection()
            
            sql = """UPDATE users SET email = %s, surname = %s, name = %s, api_key = %s, phone_number = %s WHERE id = %s"""
            values = (email, surname, name, api_key, phone_number, user_id)
            self.cursor.execute(sql, values)
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            logging.error(f"Update user error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def delete_user(self, user_id):
        """
        Deletes a user from the database.

        Parameters:
            user_id (int): The ID of the user to delete.
        

        Returns:
            bool: True if the user is deleted successfully, False otherwise.

        Raises:
            mysql.connector.Error: If the deletion fails.
        """
        try:
            self.ensure_connection()
            sql = "DELETE FROM users WHERE id = %s"
            self.cursor.execute(sql, (user_id,))
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            logging.error(f"Delete user error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def check_username_exists(self, username):
        """
        Checks if a username already exists in the database.

        Parameters:
            username (str): The username to check.


        Returns:
            bool: True if the username exists, False otherwise.

        Raises:
            mysql.connector.Error: If the operation fails.
        """
        try:
            self.ensure_connection()
            sql = "SELECT * FROM users WHERE username = %s"
            self.cursor.execute(sql, (username,))
            return self.cursor.fetchone() is not None
        except mysql.connector.Error as err:
            logging.error(f"Username check error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def check_email_exists(self, email):
        """
        Checks if an email already exists in the database.

        Parameters:
            email (str): The email to check.

        Returns:
            bool: True if the email exists, False otherwise.

        Raises:
            mysql.connector.Error: If the operation fails.
        """
        try:
            self.ensure_connection()
            sql = "SELECT * FROM users WHERE email = %s"
            self.cursor.execute(sql, (email,))
            return self.cursor.fetchone() is not None
        except mysql.connector.Error as err:
            logging.error(f"Email check error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def login_by_token(self, access_token):
        """
        Authenticates a user using their token.

        Parameters:
           access_token (str): The authentication token.

        Returns:
            dict: The user's information if the access_token'is valid, otherwise None.
        

        Raises:
            mysql.connector.Error: If the operation fails.
        """
        try:
            self.ensure_connection()
            sql = "SELECT * FROM `users` WHERE `access_token` = %s"
            self.cursor.execute(sql, (access_token,))
            return self.cursor.fetchone()
        except mysql.connector.Error as err:
            logging.error(f"Token login error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def update_user_token(self, user_id, token):
        """
        Updates the authentication access_token for a specific user.

        Parameters:
            user_id (int): The user's ID.
            access_token (str): The new token.
        

        Return:
            True: if update is sucsesfuly, False otherwise.

        Raises:
            mysql.connector.Error: If the operation fails.
        """
        try:
            sql = "UPDATE users SET access_token = %s WHERE id = %s"
            self.cursor.execute(sql, (token, user_id))
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            logging.error(f"Token update error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()

        
    # ========================= Chat Management =========================

    def create_chats_table(self):
        """
        Creates a table for storing chat information.

        Table schema:
            - id: INT (Primary key, auto-increment)
            - user_id: INT (Foreign key referencing `users.id`)
            - name: VARCHAR(50) (The name of the chat)
            - model_id: INT (Foreign key referencing `models.id`)
            - timestamp: TIMESTAMP (Default: CURRENT_TIMESTAMP)

        Example:
            >>> db = Database(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE)
            >>> db.create_chats_table()

        Raises:
            mysql.connector.Error: If the operation fails.
        """
        try:
            self.ensure_connection()
            sql = """
            CREATE TABLE IF NOT EXISTS chats (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                name VARCHAR(50),
                model_id INT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (model_id) REFERENCES models(id)
            )
            """
            self.cursor.execute(sql)
            self.connection.commit()
        except mysql.connector.Error as err:
            logging.error(f"Create chat table error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def create_table_chat_messages(self):
        """
        Creates a table for storing chat messages.

        Table schema:
            - id: INT (Primary key, auto-increment)
            - chat_id: INT (Foreign key referencing `chats.id`)
            - user_id: INT (Foreign key referencing `users.id`)
            - role: VARCHAR(100) (The role of the message sender, e.g., 'user' or 'assistant')
            - content: TEXT (The message content)
            - model_id: INT (Foreign key referencing `models.id`)
            - timestamp: TIMESTAMP (Default: CURRENT_TIMESTAMP)

        Example:
            >>> db = Database(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE)
            >>> db.create_table_chat_messages()
        Raises:
            mysql.connector.Error: If the operation fails.
        """
        try:
            self.ensure_connection()
            sql = """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_id INT,
                user_id INT,
                role VARCHAR(100),
                content TEXT,
                model_id INT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_id) REFERENCES chats(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (model_id) REFERENCES models(id)
            )
            """
            self.cursor.execute(sql)
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            logging.error(f"Create chat messages table error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def get_user_chat_list(self, user_id):
        """
        Retrieves a list of chats for a specific user. orderid by timestamp DESC.

        Parameters:
            user_id (int): The ID of the user.

        Returns:
            list[dict]: A list of dictionaries, each containing:
                - id (int): The chat ID.
                - name (str): The chat name.
                - timestamp (datetime): The creation timestamp of the chat.

        Raises:
            mysql.connector.Error: If the operation fails.
        """
        try:
            self.ensure_connection()
            sql = "SELECT id, name, timestamp FROM chats WHERE user_id = %s ORDER BY timestamp DESC"
            self.cursor.execute(sql, (user_id,))
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            logging.error(f"Get chat list error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def get_chat_data(self, chat_id, user_id):
        """
        Retrieves the messages of a specific chat for a user.

        Parameters:
            chat_id (int): The ID of the chat.
            user_id (int): The ID of the user.

        Returns:
            list[dict]: A list of messages with details (role, content, timestamp, etc.).


        Raises:
            mysql.connector.Error: If the operation fails.
        """
        try:
            self.ensure_connection()
            sql = "SELECT * FROM chat_messages WHERE chat_id = %s AND user_id = %s"
            self.cursor.execute(sql, (chat_id, user_id))
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            logging.error(f"Get chat data error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def create_new_chat(self, user_id, name, model_id):
        """
        Creates a new chat for the user.

        Parameters:
            user_id (int): The ID of the user.
            name (str): The name of the chat.
            model_id (int): The ID of the model associated with the chat.
        

        Returns:
            int: The ID of the newly created chat.

        Raises:
            mysql.connector.Error: If the operation fails.
        """
        try:
            self.ensure_connection()
            sql = "INSERT INTO chats (user_id, name, model_id) VALUES (%s, %s, %s)"
            self.cursor.execute(sql, (user_id, name, model_id))
            self.connection.commit()
            return self.cursor.lastrowid
        except mysql.connector.Error as err:
            logging.error(f"Create new chat error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def update_chat_name(self, chat_id, name) -> bool | None:
        """
        Updates the name of a specific chat.

        Parametirs:
            chat_id (int): The ID of the chat to update.
            name (str): The new name for the chat.


        Return:
            bool: True if the update was successful, False otherwise.
        Raises:
            mysql.connector.Error: If the operation fails.
        """
        try:
            self.ensure_connection()
            sql = "UPDATE chats SET name = %s WHERE id = %s"
            self.cursor.execute(sql, (name, chat_id))
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            logging.error(f"Update chat model error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()



    def save_chat_message(self, chat_id, user_id, role, content, model_id) -> bool | None:
        """
        Saves a chat message in the database.

        Parameters:
            chat_id (int): The ID of the chat.
            user_id (int): The ID of the user sending the message.
            role (str): The role of the message sender (e.g., 'user', 'assistant').
            content (str): The message content.
            model_id (int): The ID of the model used for the chat.

        Return:
            bool: True if the message was saved successfully, False otherwise.

        Raises:
            mysql.connector.Error: If the operation fails.
        """
        try:
            self.ensure_connection()
            sql = "INSERT INTO chat_messages (chat_id, user_id, role, content, model_id) VALUES (%s, %s, %s, %s, %s)"
            self.cursor.execute(sql, (chat_id, user_id, role, content, model_id))
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            logging.error(f"Save chat message error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def delete_chat(self, chat_id, user_id) -> bool | None:
        """
        Deletes a chat for a user.

        Parameters:
            chat_id (int): The ID of the chat to delete.
            user_id (int): The ID of the user.


        Return:
            bool: True if delete chat sucsesfuly, False otherwise.

        Raises:
            mysql.connector.Error: If the operation fails.
        """
        try:
            self.ensure_connection()
            sql = "DELETE FROM chats WHERE id = %s AND user_id = %s"
            self.cursor.execute(sql, (chat_id, user_id))
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            logging.error(f"Delete chat error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def delete_chat_messages(self, chat_id, user_id) -> bool | None:
        """
        Deletes all messages from a specific chat for a user.

        Parameters:
            chat_id (int): The ID of the chat from which messages should be deleted.
            user_id (int): The ID of the user owning the chat.
        

        Return:
            bool: True if delete chat messages sucsesfuly, False otherwise.

        Raises:
            mysql.connector.Error: If the operation fails.
        """
        try:
            self.ensure_connection()
            sql = "DELETE FROM chat_messages WHERE chat_id = %s AND user_id = %s"
            self.cursor.execute(sql, (chat_id, user_id))
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            logging.error(f"Delete chat messages error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def get_chat_messages(self, chat_id, user_id) -> List[Dict]:
        """
        Retrieves all messages associated with a specific chat for a given user.

        Parameters:
            chat_id (int): The ID of the chat to retrieve messages from.
            user_id (int): The ID of the user for whom to retrieve messages.


        Returns:
            list[dict]: A list of dictionaries, each containing:
                - id: INT (Message ID)
                - chat_id: INT (Chat ID)
                - user_id: INT (User ID)
                - content: TEXT (Message content)
                - created_at: TIMESTAMP (Message creation timestamp)

        Raises:
            mysql.connector.Error: If the query fails.
        """
        try:
            self.ensure_connection()
            sql = "SELECT * FROM chat_messages WHERE chat_id = %s AND user_id = %s"
            self.cursor.execute(sql, (chat_id, user_id))
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            logging.error(f"Get model infos error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def get_chat_info(self, chat_id, user_id) -> Dict | None:
        """
        Retrieves the name of a specific chat for a user.

        Parameters:
            chat_id (int): The ID of the chat.
            user_id (int): The ID of the user owning the chat.
        

        Returns:
            dict: A dictionary containing the chat name, or None if the chat doesn't exist.

        Raises:
            mysql.connector.Error: If the operation fails.
        """
        try:
            self.ensure_connection()
            sql = "SELECT * FROM chats WHERE id = %s AND user_id = %s"
            self.cursor.execute(sql, (chat_id, user_id))
            result = self.cursor.fetchone()
            return result
        except mysql.connector.Error as err:
            logging.error(f"Get chat name error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


# ========================= Password Utilities =========================
    def hash_password(self, password) -> str | None:
        """
        Hashes a plaintext password using the SHA-256 algorithm.

        Parameters:
            password (str): The plaintext password to hash.

        Returns:
            str: A string representing the hashed password.

        How it works:
            - The `hashlib` module is used to apply the SHA-256 hash function to the provided password.
            - The password is first encoded to bytes using UTF-8 encoding.
            - The hash function processes the encoded bytes, and the resulting hash is converted back to a string.


        """
        return hashlib.sha256(password.encode()).hexdigest()


    def verify_password(self, hashed_password, user_password):
        """
        Verifies if a plaintext password matches its hashed counterpart.

        Parameters:
            hashed_password (str): The hashed password stored in the database.
            user_password (str): The plaintext password provided by the user.

        Returns:
            bool: True if the hashed version of `user_password` matches `hashed_password`, False otherwise.

        How it works:
            - The `user_password` is hashed using the same SHA-256 algorithm.
            - The resulting hash is compared with the stored `hashed_password`.
            - If the hashes match, the function returns `True`, indicating the passwords are the same.


        """
        return hashed_password == hashlib.sha256(user_password.encode()).hexdigest()

    # ========================= Model Management =========================

    def create_table_models(self) -> None:
        """
        Creates a table for storing AI model information and pre-populates it with default models.

        Table schema:
            - id: INT (Primary key, auto-increment)
            - name: VARCHAR(255) (Name of the model, not null)
            - description: TEXT (Description of the model)
            - type: VARCHAR(255) (Type of the model, e.g., 'chat', not null)
            - system: TEXT (System promt for model)
            - visibility: VARCHAR(30): Visibility of model.
            - creator_id: INT (Foreign key referencing the users table)
            - created_date: TIMESTAMP (Default: CURRENT_TIMESTAMP)
            - max_token: INT (Maximum token limit for the model)
            - admin_acsess: BOOLEAN DEAFAULT 1 (Indicates if the model requires admin access)

        Pre-populated models:
            - gpt-4o-mini
            - gpt-3.5-turbo
            - gpt-4


        Raises:
            mysql.connector.Error: If the table creation or insertion of default models fails.
        """
        try:
            sql = """
                CREATE TABLE IF NOT EXISTS `models` (
                    `id` INT AUTO_INCREMENT PRIMARY KEY,
                    `name` VARCHAR(255) NOT NULL,
                    `description` TEXT,
                    `system` TEXT,
                    `visibility` BOOLEAN DEFAULT 0,
                    `max_tokens` INT,
                    `creator_id` INT,
                    `admin_access` BOOLEAN DEFAULT 1,
                    `type` VARCHAR(255) NOT NULL,
                    `doc_id` VARCHAR(255),
                    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (creator_id) REFERENCES users(id)
                );
            """
            self.cursor.execute(sql)
            self.connection.commit()

            models = [
                ("gpt-4o-mini", "More capable than any GPT-3.5 model, optimized for chat. Updated with the latest iteration.", "chat", 1),
                ("gpt-3.5-turbo", "Most capable GPT-3.5 model, optimized for chat at 1/10th the cost of text-davinci-003.", "chat", 1),
                ("gpt-4", "More capable than any GPT-3.5 model, optimized for complex tasks and chat.", "chat", 1),
                ("Llama 13b chat", "Llama 2 is a collection of pretrained and fine-tuned generative text models ranging in scale from 7 billion to 70 billion parameters.", "llama", 1),
            ]

            for model in models:
                self.cursor.execute("SELECT * FROM models WHERE name = %s", (model[0],))
                if self.cursor.fetchone() is None:
                    self.cursor.execute("INSERT INTO models (name, description, type, visibility) VALUES (%s, %s, %s, %s)", model)
                    self.connection.commit()
        except mysql.connector.Error as err:
            logging.error(f"Create models table error: {err}")
            self.reconnect()
            self.reconnect()
        finally:
            self.cursor.nextset()


    def insert_model(self,
                     name: str, 
                     description: str, 
                     system: str, 
                     visibility: bool, 
                     max_tokens: int, 
                     creator_id: int,  
                     doc_id: str,
                     model_type: str) -> bool | None:
        """ 
        Inserts a new AI model into the database.

        Args:
            name (str): The name of the model.
            description (str): The description of the model.
            type (str): The type of the model.
            system (str): The system prompt for the model.
            visibility (bool): The visibility of the model.
            max_tokens (int): The maximum token limit for the model.
            creator_id (int): The ID of the user who created the model.
            doc_id (str): The ID of the document associated with the model.


        Return:
            bool: True if create sucsesfully, False otherwise.
            
        Raises:
            mysql.connector.Error: If the model insertion fails.
        """
        try:
            sql = """INSERT INTO  `models` (`name`, `description`, `type`, `system`, `visibility`, `max_tokens`, `creator_id`, `doc_id`)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"""
            values = (name, description, model_type, system, visibility, max_tokens, creator_id, doc_id)
            self.cursor.execute(sql, values)
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            logging.error(f"Insert model error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def update_model(self, model_id: int, name: str, description: str, type: str, system: str, visibility: bool, max_tokens: int, doc_id: str):
        """
        Updates an existing AI model in the database.

        Args:
            model_id (int): The ID of the model to update.
            name (str): The new name of the model.
            description (str): The new description of the model.
            type (str): The new type of the model.
            system (str): The new system prompt for the model.
            visibility (bool): The new visibility of the model.
            max_tokens (int): The new maximum token limit for the model.
            doc_id (str): The new ID of the document associated with the model.


        Raises:
            mysql.connector.Error: If the model update fails.
        """
        try:
            sql = """UPDATE models
                     SET name = %s, description = %s, type = %s, system = %s, visibility = %s, max_tokens = %s, doc_id = %s
                     WHERE id = %s"""
            values = (name, description, type, system, visibility, max_tokens, doc_id, model_id)
            self.cursor.execute(sql, values)
            self.connection.commit()
        except mysql.connector.Error as err:
            logging.error(f"Update model error: {err}")


    def delete_model(self, model_id: int, user_id: int) -> bool | None:
        """
        Deletes an AI model from the database.
        Args:
            model_id (int): The ID of the model to delete.
            user_id (int): The ID of the user attempting to delete the model.


        Raises:
            mysql.connector.Error: If the model deletion fails.
        """
        try:
            sql = "DELETE FROM models WHERE id = %s AND creator_id = %s"
            values = (model_id, user_id)
            self.cursor.execute(sql, values)
            self.connection.commit()
            return True
        except mysql.connector.Error as err:
            logging.error(f"Delete model error: {err}")


    def get_models_list(self, user_id) -> Dict | None:
        """
        Retrieves a list of all AI models available in the database.

        Parametirs:
            user_id (int): specific ID for user.


        Returns:
            list[dict]: A list of dictionaries, each containing:
                - id: INT (Model ID)
                - name: VARCHAR(255) (Model name)
                - description: TEXT (Model description)
                - type: VARCHAR(255) (Model type)
                - created_at: TIMESTAMP (Model creation timestamp)

        Raises:
            mysql.connector.Error: If the query fails.
        """
        try:
            self.ensure_connection()
            self.ensure_connection()
            sql = "SELECT * FROM models WHERE creator_id = %s or visibility=1"
            self.cursor.execute(sql, (user_id, ))
            return self.cursor.fetchall()
        except mysql.connector.Error as err:
            logging.error(f"Get models list error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def check_model_exists(self, model_name):
        """
        Checks if a specific model exists in the database.

        Parameters:
            model_name (str): The name of the model to check.


        Returns:
            bool: True if the model exists, False otherwise.

        Raises:
            mysql.connector.Error: If the query fails.
        """
        try:
            self.ensure_connection()
            sql = "SELECT * FROM models WHERE name = %s"
            self.cursor.execute(sql, (model_name,))
            return self.cursor.fetchone() is not None
        except mysql.connector.Error as err:
            logging.error(f"Check model exists error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def update_chat_model(self, chat_id, model_id):
        """
        Updates the AI model associated with a specific chat.

        Parameters:
            chat_id (int): The ID of the chat to update.
            model_id (int): The ID of the new model to associate with the chat.


        Raises:
            mysql.connector.Error: If the update fails.
        """
        try:
            self.ensure_connection()
            sql = "UPDATE chats SET model_id = %s WHERE id = %s"
            self.cursor.execute(sql, (model_id, chat_id))
            self.connection.commit()
        except mysql.connector.Error as err:
            logging.error(f"Update chat model error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    def get_model_infos(self,user_id:int, model_name=None, model_id=None) -> Dict | None:
        """
        Retrieves detailed information about a specific model.
        The model can be identified by either its name or its ID.
        At least one of the parameters (model_name or model_id) must be provided.

        Parameters:
            model_id (int): The ID of the model to retrieve.
            model_name (int): The name of the model to retrieve.
        Example:

            >>> db = Database(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE)
            >>> model_info = db.get_model_infos(1, model_name='model Name')
            >>> model_info = db.get_model_infos(1, model_id=123)

        Returns:
            dict: A dictionary containing:
                - id: INT (Model ID)
                - name: VARCHAR(255) (Model name)
                - description: TEXT (Model description)
                - type: VARCHAR(255) (Model type)
                - created_at: TIMESTAMP (Model creation timestamp)

        Raises:
            mysql.connector.Error: If the query fails.
        """
        try:
            self.ensure_connection()
            if model_name:
                sql = "SELECT * FROM models WHERE name = %s and (creator_id = %s or visibility=1)"
                self.cursor.execute(sql, (model_name, user_id))
            if model_id:
                sql = "SELECT * FROM models WHERE id = %s and (creator_id = %s or visibility=1)"
                self.cursor.execute(sql, (model_id, user_id))
            return self.cursor.fetchone()
        except mysql.connector.Error as err:
            logging.error(f"Get model infos error: {err}")
            self.reconnect()
        finally:
            self.cursor.nextset()


    # ========================= Closing Resources =========================

    def close(self):
        """
        Closes the database connection and associated cursor.

        Notes:
            This method should be called after all database operations are completed to ensure
            proper resource cleanup.

        Example:
            >>> db = Database(host="localhost", user="root", password="password", database="testdb")
            >>> db.close()

        """
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()


    def __del__(self):
        """
        Ensures the database connection is closed when the object is deleted.
        """
        self.close()

