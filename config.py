import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'sas-secret-2024')
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'sas.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
    GROQ_MODEL   = 'llama3-8b-8192'
