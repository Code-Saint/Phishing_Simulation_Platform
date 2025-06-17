import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'phish-secret'
    DATABASE = os.path.join('instance', 'phishing.db')
