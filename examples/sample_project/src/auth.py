"""사용자 인증 서비스 모듈"""
import hashlib
from src.database import Database


class AuthService:
    def __init__(self):
        self.db = Database()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def login(self, username, password):
        hashed = self.hash_password(password)
        user = self.db.fetch_one(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, hashed)
        )
        if user:
            return {"success": True, "user_id": user["id"]}
        return {"success": False, "error": "Invalid credentials"}

    def register(self, username, password, email):
        hashed = self.hash_password(password)
        try:
            self.db.execute(
                "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                (username, hashed, email)
            )
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
