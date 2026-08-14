"""Load environment settings and library rules."""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load local environment values when available.
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'elibrary-super-secret-key-2026')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///elibrary.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Settings for the AI service proxy.
    AI_BASE_URL = os.getenv('AI_BASE_URL', 'https://your-api-key')
    AI_API_TOKEN = os.getenv('AI_API_TOKEN', 'xx-API-token')
    
    # Rules used while issuing and returning books.
    MAX_BORROW_LIMIT = 5
    DEFAULT_LOAN_DAYS = 14
    DAILY_FINE_RATE = 1.50
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
