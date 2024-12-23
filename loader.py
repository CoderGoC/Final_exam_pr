from db.database import Database
from models.llm import LLM
from data.config import (
    MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
)


db = Database(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE)

db.create_user_table()



model = LLM()
