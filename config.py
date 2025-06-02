import os
from dotenv import load_dotenv

# Carrega variáveis do .env apenas fora do Render
if not os.getenv("RENDER"):
    load_dotenv(".env")

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    BRASIL_ABERTO_API_KEY = os.getenv('BRASIL_ABERTO_API_KEY')
    DEBUG = os.getenv('DEBUG', 'False').lower() in ['true', '1', 'yes']
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024


   
