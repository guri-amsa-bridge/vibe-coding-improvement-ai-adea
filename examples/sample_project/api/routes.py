"""API 라우팅 모듈 — 각 서비스를 HTTP 엔드포인트로 연결"""
from src.user_service import UserService
from src.auth import AuthService
from src.item_service import ItemService


user_service = UserService()
auth_service = AuthService()
item_service = ItemService()


def handle_login(request):
    username = request.get("username")
    password = request.get("password")
    return auth_service.login(username, password)


def handle_register(request):
    return auth_service.register(
        request.get("username"),
        request.get("password"),
        request.get("email"),
    )


def handle_get_user(request):
    user_id = request.get("user_id")
    return user_service.get_user(user_id)


def handle_list_items(request):
    category = request.get("category")
    return item_service.list_items(category=category)


def handle_create_item(request):
    return item_service.create_item(
        request.get("name"),
        request.get("price"),
        request.get("category"),
    )
