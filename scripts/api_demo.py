"""Прогон сценариев тестирования RBAC (тесты 1-3, эскалация привилегий, IDOR).

Запросы выполняются к приложению на отдельной временной базе; протокол каждого
сценария сохраняется в reports/api/*.txt.  Запуск:  python scripts/api_demo.py
"""
import json
import os
import sys
import tempfile
from http import HTTPStatus
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "demo.db")
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)
lines = []


def say(text=""):
    lines.append(text)
    print(text)


def login(username, password):
    response = client.post("/api/v1/login", json={"username": username, "password": password})
    return response.json()["access_token"]


def call(method, path, token, who, body=None):
    """Выполняет запрос и записывает его вместе с ответом в протокол."""
    response = client.request(method, path, json=body, headers={"Authorization": f"Bearer {token}"})
    say(f"{method} {path}    [токен пользователя {who}]")
    if body is not None:
        say("  тело запроса: " + json.dumps(body, ensure_ascii=False))
    say(f"  ответ: {response.status_code} {HTTPStatus(response.status_code).phrase}")
    say("  " + json.dumps(response.json(), ensure_ascii=False))
    say()
    return response


def save(name):
    out = ROOT / "reports" / "api"
    out.mkdir(parents=True, exist_ok=True)
    (out / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    lines.clear()


admin = login("admin", "Admin123!")
user = login("user", "User123!")

say("Тест 1 (позитивный): администратор создаёт пользователя")
say()
created = call("POST", "/api/v1/admin/users", admin, "admin",
               {"username": "ivanov", "password": "Password1!", "role": "USER"}).json()
save("test1.txt")

say("Тест 2 (негативный): рядовой сотрудник обращается к /api/v1/admin/users")
say()
call("GET", "/api/v1/admin/users", user, "user")
call("POST", "/api/v1/admin/users", user, "user",
     {"username": "hacker", "password": "Password1!", "role": "ADMIN"})
save("test2.txt")

say("Тест 3: смена роли в БД «на лету», токен пользователя ivanov не перевыпускается")
say()
ivanov = login("ivanov", "Password1!")
say("Шаг 1. Роль USER: аудит недоступен")
call("GET", "/api/v1/moderator/audit", ivanov, "ivanov")
say("Шаг 2. Администратор меняет роль на MODERATOR")
call("PUT", f"/api/v1/admin/users/{created['id']}/role", admin, "admin", {"role": "MODERATOR"})
say("Шаг 3. Тот же токен: доступ появился сразу")
response = client.get("/api/v1/moderator/audit", headers={"Authorization": f"Bearer {ivanov}"})
say("GET /api/v1/moderator/audit    [токен пользователя ivanov]")
say(f"  ответ: {response.status_code} {HTTPStatus(response.status_code).phrase}")
say()
say("Шаг 4. Администратор возвращает роль USER")
call("PUT", f"/api/v1/admin/users/{created['id']}/role", admin, "admin", {"role": "USER"})
say("Шаг 5. Тот же токен: доступ снова закрыт")
call("GET", "/api/v1/moderator/audit", ivanov, "ivanov")
save("test3.txt")

say("Эскалация привилегий и IDOR")
say()
say("Пользователь ivanov пытается назначить себе роль ADMIN")
call("PUT", f"/api/v1/admin/users/{created['id']}/role", ivanov, "ivanov", {"role": "ADMIN"})
say("Пользователь ivanov подставляет в адрес чужой id (профиль администратора)")
call("GET", "/api/v1/users/1", ivanov, "ivanov")
say("Свой профиль пользователю доступен")
call("GET", f"/api/v1/users/{created['id']}", ivanov, "ivanov")
save("attacks.txt")
