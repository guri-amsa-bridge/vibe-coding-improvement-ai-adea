"""상품 관리 서비스 모듈"""
from src.database import Database


class ItemService:
    def __init__(self):
        self.db = Database()

    def get_item(self, item_id):
        return self.db.fetch_one(
            "SELECT * FROM items WHERE id=?",
            (item_id,)
        )

    def list_items(self, category=None, limit=20):
        if category:
            return self.db.fetch_all(
                "SELECT * FROM items WHERE category=? LIMIT ?",
                (category, limit)
            )
        return self.db.fetch_all("SELECT * FROM items LIMIT ?", (limit,))

    def create_item(self, name, price, category):
        self.db.execute(
            "INSERT INTO items (name, price, category) VALUES (?, ?, ?)",
            (name, price, category)
        )
        return {"success": True}
