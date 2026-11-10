"""RBAC-сервис: вход по логину и паролю, три ресурса с разным уровнем доступа."""
import sqlite3
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from app import database
from app.auth import (check_permission, create_token, get_current_user, hash_password,
                      require_role, verify_password)

app = FastAPI(title="ПР5: RBAC-сервис")

# Демонстрационные учётные записи (создаются при первом запуске)
DEMO_USERS = [
    ("admin", "Admin123!", "ADMIN"),
    ("moder", "Moder123!", "MODERATOR"),
    ("user", "User123!", "USER"),
]

database.create_tables()
for name, password, role in DEMO_USERS:
    if database.find_user(name) is None:
        database.create_user(name, hash_password(password), role)


class LoginIn(BaseModel):
    username: str
    password: str


class UserIn(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern="^[A-Za-z0-9_]+$")
    password: str = Field(min_length=8, max_length=100)
    role: Literal["ADMIN", "MODERATOR", "USER"] = "USER"


class RoleIn(BaseModel):
    role: Literal["ADMIN", "MODERATOR", "USER"]


@app.post("/api/v1/login")
def login(body: LoginIn):
    user = database.find_user(body.username)
    if user is None or not user["is_active"] or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Неверный логин или пароль")
    return {"access_token": create_token(user["id"]), "token_type": "bearer"}


# 1. Доступно всем авторизованным пользователям
@app.get("/api/v1/public")
def public(current_user=Depends(get_current_user)):
    return {"message": f"Здравствуйте, {current_user['username']}!",
            "roles": sorted(database.get_roles(current_user["id"])),
            "permissions": sorted(database.get_permissions(current_user["id"]))}


# 2. Доступно только ролям MODERATOR и ADMIN
@app.get("/api/v1/moderator/audit")
def audit(current_user=Depends(require_role("MODERATOR", "ADMIN"))):
    return {"requested_by": current_user["username"], "users": database.list_users()}


# 3. Доступно только роли ADMIN с правом MANAGE_USERS
@app.get("/api/v1/admin/users", dependencies=[Depends(require_role("ADMIN"))])
def list_users(current_user=Depends(check_permission("MANAGE_USERS"))):
    return database.list_users()


@app.post("/api/v1/admin/users", status_code=201, dependencies=[Depends(require_role("ADMIN"))])
def create_user(body: UserIn, current_user=Depends(check_permission("MANAGE_USERS"))):
    try:
        user_id = database.create_user(body.username, hash_password(body.password), body.role)
    except sqlite3.IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, "Пользователь уже существует")
    return {"id": user_id, "username": body.username, "role": body.role}


@app.put("/api/v1/admin/users/{user_id}/role", dependencies=[Depends(require_role("ADMIN"))])
def change_role(user_id: int, body: RoleIn, current_user=Depends(check_permission("MANAGE_USERS"))):
    if database.get_user(user_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    database.set_role(user_id, body.role)
    return {"id": user_id, "role": body.role}


# Защита от IDOR: чужой профиль виден только обладателю права MANAGE_USERS
@app.get("/api/v1/users/{user_id}")
def profile(user_id: int, current_user=Depends(get_current_user)):
    is_owner = user_id == current_user["id"]
    if not is_owner and "MANAGE_USERS" not in database.get_permissions(current_user["id"]):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Недостаточно прав для выполнения операции")
    user = database.get_user(user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Пользователь не найден")
    return {"id": user["id"], "username": user["username"], "roles": sorted(database.get_roles(user_id))}
