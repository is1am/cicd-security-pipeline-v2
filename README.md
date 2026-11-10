# ПР5 — RBAC-сервис и CI/CD Security Pipeline (SAST + SCA)

Сервис на FastAPI с ролевой моделью доступа и пайплайн, который при каждом push
и pull request проверяет код (Bandit), зависимости (pip-audit) и тесты ролей (pytest).

## Что где лежит

| Файл | Назначение |
| --- | --- |
| `app/database.py` | пять таблиц RBAC и запросы к ним (SQLite) |
| `app/auth.py` | JWT-токен, `get_current_user`, `require_role`, `check_permission` |
| `app/main.py` | эндпоинты |
| `tests/test_rbac.py` | 8 тестов ролевой модели |
| `.github/workflows/security.yml` | пайплайн GitHub Actions |
| `.gitlab-ci.yml` | тот же пайплайн для GitLab CI |
| `sql/rbac_schema.sql` | схема БД для PostgreSQL |
| `postman/` | коллекция Postman с тестами 1–3 |
| `reports/` | вывод сканеров до и после исправлений, протоколы запросов к API |
| `report/` | скрипты сборки отчёта и рисунки |

Репозиторий: https://github.com/is1am/cicd-security-pipeline-v2

В истории git первый коммит — версия с уязвимостями (пайплайн падает),
следующий — исправления (пайплайн проходит).

## Установка и запуск

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt -r requirements-dev.txt
.venv\Scripts\python -m uvicorn app.main:app
```

Swagger UI: http://127.0.0.1:8000/docs. Учётные записи: `admin / Admin123!`,
`moder / Moder123!`, `user / User123!`.

## Проверки, которые выполняет пайплайн

```
.venv\Scripts\python -m bandit -r app -ll
.venv\Scripts\python -m pip_audit -r requirements.txt
.venv\Scripts\python -m pytest -q
```

## Тесты в Postman

Запустите сервис, импортируйте `postman/RBAC_PR5.postman_collection.json`
и выполните Run collection: запросы идут по порядку, токены сохраняются сами.

## Отчёт

```
.venv\Scripts\python scripts\api_demo.py
python report\make_images.py
python report\build_report.py
```

Для сборки отчёта нужны `python-docx` и `pillow`.
