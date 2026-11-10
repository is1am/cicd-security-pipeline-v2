"""Аутентификация (JWT) и авторизация (проверка ролей и разрешений)."""
import hashlib
import time

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app import database

SECRET_KEY = "supersecret123"
TOKEN_TTL = 3600  # срок жизни токена, секунд

bearer = HTTPBearer(auto_error=False)


def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()


def verify_password(password, stored):
    return hash_password(password) == stored


def create_token(user_id):
    # В токене только id пользователя: роли и права каждый раз читаются из БД
    payload = {"sub": str(user_id), "exp": int(time.time()) + TOKEN_TTL}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def get_current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer)):
    """Аутентификация: кто делает запрос. Без действительного токена — 401."""
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Требуется токен")
    try:
        payload = jwt.decode(cred.credentials, SECRET_KEY, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Недействительный токен")
    user = database.get_user(int(payload["sub"]))
    if user is None or not user["is_active"]:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Учётная запись неактивна")
    return {"id": user["id"], "username": user["username"]}


def require_role(*allowed_roles):
    """Авторизация по роли: у пользователя должна быть хотя бы одна из ролей."""
    def dependency(current_user=Depends(get_current_user)):
        user_roles = database.get_roles(current_user["id"])
        if not user_roles & set(allowed_roles):
            raise HTTPException(status.HTTP_403_FORBIDDEN,
                                "Недостаточно прав для выполнения операции")
        return current_user
    return dependency


def check_permission(required_permission):
    """Авторизация по разрешению: оно должно быть у одной из ролей пользователя."""
    def dependency(current_user=Depends(get_current_user)):
        user_permissions = database.get_permissions(current_user["id"])
        if required_permission not in user_permissions:
            raise HTTPException(status.HTTP_403_FORBIDDEN,
                                "Недостаточно прав для выполнения операции")
        return current_user
    return dependency
