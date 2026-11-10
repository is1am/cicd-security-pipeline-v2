"""Тесты ролевой модели: позитивные и негативные сценарии из методических указаний."""
import uuid

ADMIN = ("admin", "Admin123!")
MODER = ("moder", "Moder123!")
USER = ("user", "User123!")


def new_user(client, admin_headers, role="USER"):
    """Создаёт пользователя с уникальным именем, возвращает (id, имя, пароль)."""
    name = "u_" + uuid.uuid4().hex[:8]
    response = client.post("/api/v1/admin/users", headers=admin_headers,
                           json={"username": name, "password": "Password1!", "role": role})
    assert response.status_code == 201
    return response.json()["id"], name, "Password1!"


def test_request_without_token_is_rejected(client):
    assert client.get("/api/v1/public").status_code == 401


def test_public_is_available_to_every_role(client, login):
    for account in (ADMIN, MODER, USER):
        assert client.get("/api/v1/public", headers=login(*account)).status_code == 200


# Тест 1 (позитивный): администратор создаёт пользователя
def test_admin_can_create_user(client, login):
    user_id, name, _ = new_user(client, login(*ADMIN))
    users = client.get("/api/v1/admin/users", headers=login(*ADMIN)).json()
    assert {"id": user_id, "username": name, "is_active": True, "roles": ["USER"]} in users


# Тест 2 (негативный): рядовой сотрудник не попадает в административный раздел
def test_user_cannot_open_admin_endpoint(client, login):
    headers = login(*USER)
    assert client.get("/api/v1/admin/users", headers=headers).status_code == 403
    response = client.post("/api/v1/admin/users", headers=headers,
                           json={"username": "hacker", "password": "Password1!", "role": "ADMIN"})
    assert response.status_code == 403


def test_moderator_sees_audit_but_not_admin(client, login):
    headers = login(*MODER)
    assert client.get("/api/v1/moderator/audit", headers=headers).status_code == 200
    assert client.get("/api/v1/admin/users", headers=headers).status_code == 403


# Тест 3: роль меняется в БД «на лету», токен остаётся прежним
def test_role_change_applies_without_new_token(client, login):
    admin_headers = login(*ADMIN)
    user_id, name, password = new_user(client, admin_headers)
    headers = login(name, password)  # токен выдан, пока роль — USER

    assert client.get("/api/v1/moderator/audit", headers=headers).status_code == 403

    client.put(f"/api/v1/admin/users/{user_id}/role", headers=admin_headers, json={"role": "MODERATOR"})
    assert client.get("/api/v1/moderator/audit", headers=headers).status_code == 200

    client.put(f"/api/v1/admin/users/{user_id}/role", headers=admin_headers, json={"role": "USER"})
    assert client.get("/api/v1/moderator/audit", headers=headers).status_code == 403


# Эскалация привилегий: пользователь пытается сам назначить себе роль ADMIN
def test_user_cannot_promote_himself(client, login):
    admin_headers = login(*ADMIN)
    user_id, name, password = new_user(client, admin_headers)
    response = client.put(f"/api/v1/admin/users/{user_id}/role", headers=login(name, password),
                          json={"role": "ADMIN"})
    assert response.status_code == 403


# IDOR: подстановка чужого id в адрес запроса
def test_user_cannot_read_foreign_profile(client, login):
    admin_headers = login(*ADMIN)
    first_id, name, password = new_user(client, admin_headers)
    second_id, _, _ = new_user(client, admin_headers)
    headers = login(name, password)

    assert client.get(f"/api/v1/users/{first_id}", headers=headers).status_code == 200
    assert client.get(f"/api/v1/users/{second_id}", headers=headers).status_code == 403
    assert client.get(f"/api/v1/users/{second_id}", headers=admin_headers).status_code == 200
