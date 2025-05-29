import os
from dotenv import load_dotenv

if not os.getenv("RENDER"):  # variável só existe no Render
    load_dotenv(".env")

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

    DEBUG = os.getenv('DEBUG', True)

    # Caminho para uploads de arquivos
    UPLOAD_FOLDER = os.path.join('static', 'uploads')

    # Tamanho máximo de upload (ex: 16 MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024




   
