import os
from dotenv import load_dotenv

load_dotenv()


#Over here all the configurations are added within this class
class Config:
    API_KEY = os.getenv('GEMINI_API_KEY')
    DB_PATH = 'blog.db'
    UPLOAD_FOLDER = 'static/uploads'
    BAD_WORDS = ["fuck", "shit", "damn", "bitch", "fuckoff"]
    GEMINI_MODEL="gemma-3-1b-it"