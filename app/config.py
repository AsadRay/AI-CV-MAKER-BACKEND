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

    IMAP_SERVER = os.getenv('IMAP_SERVER')

    IMAP_PORT = int(os.getenv('IMAP_PORT'))

    MAIL_SERVER = os.getenv('MAIL_SERVER')

    MAIL_PORT = int(os.getenv('MAIL_PORT'))

    MAIL_USERNAME = os.getenv('MAIL_USERNAME')

    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')

    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS') == 'True'

    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL') == 'True'

    MAIL_ASCII_ATTACHMENTS = os.getenv('MAIL_ASCII_ATTACHMENTS') == 'True'
