import os
from environs import Env


env = Env()
env.read_env()


MYSQL_HOST = env.str('MYSQL_HOST')
MYSQL_USER = env.str('MYSQL_USER')
MYSQL_PASSWORD = env.str('MYSQL_PASSWORD')
MYSQL_DATABASE = env.str('MYSQL_DATABASE')
REPLECATE_API = env.str('REPLECATE_API')

VECTOR_STORAGE_DIR = "./document_vectorstores"
METADATA_FILE = os.path.join(VECTOR_STORAGE_DIR, "document_metadata.json")

