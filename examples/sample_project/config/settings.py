"""애플리케이션 설정"""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
API_VERSION = "v1"
MAX_LOGIN_ATTEMPTS = 5
