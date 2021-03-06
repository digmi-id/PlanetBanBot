import os
from dotenv import load_dotenv


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))


class Config:
    API_TOKEN = os.environ.get('API_TOKEN')
    DEVELOPERS = os.environ.get('DEVELOPERS').split(',')
