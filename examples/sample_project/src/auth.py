"""사용자 인증 서비스 모듈

변경 이력:
  - JWT 스타일 토큰 기반 인증 추가
  - 비밀번호 해싱 알고리즘 강화 (salt 적용)
"""
import hashlib
import secrets
import time
from src.database import Database


class AuthService:
    TOKEN_EXPIRY = 3600  # 토큰 만료 시간 (초)

    def __init__(self):
        self.db = Database()
        self._active_tokens = {}

    def hash_password(self, password, salt=None):
        if salt is None:
            salt = secrets.token_hex(16)
        hashed = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
        return f"{salt}:{hashed}"

    def verify_password(self, password, stored_hash):
        """저장된 해시와 비밀번호를 비교 검증"""
        salt, hash_value = stored_hash.split(":")
        return self.hash_password(password, salt) == stored_hash

    def generate_token(self, user_id):
        """사용자 인증 토큰 생성"""
        token = secrets.token_urlsafe(32)
        self._active_tokens[token] = {
            "user_id": user_id,
            "created_at": time.time(),
        }
        return token

    def validate_token(self, token):
        """토큰 유효성 검증"""
        token_data = self._active_tokens.get(token)
        if not token_data:
            return {"valid": False, "error": "Token not found"}
        if time.time() - token_data["created_at"] > self.TOKEN_EXPIRY:
            del self._active_tokens[token]
            return {"valid": False, "error": "Token expired"}
        return {"valid": True, "user_id": token_data["user_id"]}

    def login(self, username, password):
        hashed = self.hash_password(password)
        user = self.db.fetch_one(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, hashed)
        )
        if user:
            token = self.generate_token(user["id"])
            return {"success": True, "user_id": user["id"], "token": token}
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

    def logout(self, token):
        """토큰 무효화(로그아웃)"""
        if token in self._active_tokens:
            del self._active_tokens[token]
            return {"success": True}
        return {"success": False, "error": "Token not found"}
