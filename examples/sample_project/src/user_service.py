"""사용자 관리 서비스 모듈"""
from src.database import Database
from src.auth import AuthService


class UserService:
    def __init__(self):
        self.db = Database()
        self.auth = AuthService()

    def get_user(self, user_id):
        return self.db.fetch_one(
            "SELECT id, username, email FROM users WHERE id=?",
            (user_id,)
        )

    def update_profile(self, user_id, email):
        self.db.execute(
            "UPDATE users SET email=? WHERE id=?",
            (email, user_id)
        )
        return {"success": True}

    def delete_user(self, user_id):
        self.db.execute("DELETE FROM users WHERE id=?", (user_id,))
        return {"success": True}

    def list_users(self, limit=50):
        return self.db.fetch_all(
            "SELECT id, username, email FROM users LIMIT ?",
            (limit,)
        )
