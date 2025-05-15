from os import getenv
from dotenv import load_dotenv

load_dotenv()

SQLITE_PATH = getenv('SQLITE_PATH')
SQLITE_TABLE_NAME = getenv('SQLITE_TABLE_NAME')

RABBITMQ_USER = getenv('QUEUE_USER')
RABBITMQ_PASS = getenv('QUEUE_PASSWORD')
RABBITMQ_HOST = getenv('QUEUE_HOST')
QUEUE_NAME = getenv('QUEUE_NAME')

SOCKET_HOST=getenv('SOCKET_HOST')
SOCKET_PORT=int(getenv('SOCKET_PORT'))

TRANSPORT=getenv('TRANSPORT')