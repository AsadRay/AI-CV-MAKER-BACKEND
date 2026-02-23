import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

    JWT_ALGORITHM = os.getenv('JWT_ALGORITHM')

    SQLALCHEMY_TRACK_MODIFICATIONS = False


    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=5)

    RESEND_API_KEY = os.getenv('RESEND_API_KEY')


    

