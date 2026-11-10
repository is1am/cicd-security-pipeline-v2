"""Сборка отчёта Отчет_ПР5.docx.  Запуск:  python report/build_report.py

Листинги берутся прямо из исходных файлов проекта, рисунки — из report/img
(их создаёт report/make_images.py).
"""
import ast
import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "report" / "img"
doc = Document()

# ---------- оформление ----------
section = doc.sections[0]
section.left_margin, section.right_margin = Cm(3), Cm(1.5)
section.top_margin, section.bottom_margin = Cm(2), Cm(2)


def set_font(style, name, size):
    style.font.name = name
    style.font.size = Pt(size)
    fonts = style.element.get_or_add_rPr().get_or_add_rFonts()
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(attr), name)
    for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        fonts.attrib.pop(qn(attr), None)  # иначе шрифт темы перекрывает заданный


set_font(doc.styles["Normal"], "Times New Roman", 14)
for level in (1, 2):
    style = doc.styles[f"Heading {level}"]
    set_font(style, "Times New Roman", 14)
    style.font.bold = True
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.paragraph_format.space_before = Pt(12)
    style.paragraph_format.space_after = Pt(6)

counters = {"рис": 0, "табл": 0, "лист": 0}


def para(text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=True, bold=False, size=None, after=0):
    p = doc.add_paragraph()
    p.alignment = align
    fmt = p.paragraph_format
    fmt.first_line_indent = Cm(1.25) if indent else None
    fmt.line_spacing = 1.15
    fmt.space_after = Pt(after)
    run = p.add_run(text)
    run.bold = bold
    if size:
        run.font.size = Pt(size)
    return p


def center(text, bold=False, size=None, after=0):
    return para(text, WD_ALIGN_PARAGRAPH.CENTER, indent=False, bold=bold, size=size, after=after)


def bullets(items):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(0)
        p.add_run(item)


def figure(name, caption, width=16.0):
    counters["рис"] += 1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(IMG / name), width=Cm(width))
    center(f"Рисунок {counters['рис']} — {caption}", size=12, after=8)


def listing(code, caption):
    counters["лист"] += 1
    table = doc.add_table(rows=1, cols=1)
    table.style = "Table Grid"
    cell = table.rows[0].cells[0]
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(code.rstrip("\n"))
    run.font.name = "Consolas"
    run.font.size = Pt(9)
    run._element.rPr.rFonts.set(qn("w:cs"), "Consolas")
    center(f"Листинг {counters['лист']} — {caption}", size=12, after=8)


def table(caption, header, rows, widths):
    counters["табл"] += 1
    p = para(f"Таблица {counters['табл']} — {caption}", WD_ALIGN_PARAGRAPH.LEFT, indent=False, size=12)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.keep_with_next = True
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for row_index, row in enumerate([header] + rows):
        cells = t.rows[0].cells if row_index == 0 else t.add_row().cells
        for i, value in enumerate(row):
            cells[i].width = Cm(widths[i])
            cell_p = cells[i].paragraphs[0]
            cell_p.paragraph_format.space_after = Pt(0)
            run = cell_p.add_run(str(value))
            run.font.size = Pt(11)
            run.bold = row_index == 0
            if row_index == 0:
                shade = OxmlElement("w:shd")
                shade.set(qn("w:val"), "clear")
                shade.set(qn("w:fill"), "D9E2F3")
                cells[i]._element.get_or_add_tcPr().append(shade)
    para("", indent=False, size=6)


def source(path, *names):
    """Текст перечисленных функций (вместе с декораторами) из файла проекта."""
    text = (ROOT / path).read_text(encoding="utf-8")
    lines = text.splitlines()
    nodes = {n.name: n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef)}
    parts = []
    for name in names:
        node = nodes[name]
        start = min([node.lineno] + [d.lineno for d in node.decorator_list])
        while start > 1 and lines[start - 2].startswith("#"):  # комментарий над функцией
            start -= 1
        parts.append("\n".join(lines[start - 1:node.end_lineno]))
    return "\n\n\n".join(parts)


def read(path):
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


# ---------- титульный лист ----------
center("МИНИСТЕРСТВО ОБРАЗОВАНИЯ И НАУКИ КАЗАХСТАН", bold=True)
center("«НАО Евразийский национальный университет имени Л. Н. Гумилёва»", bold=True)
center("Факультет информационных технологий")
center("Кафедра Информационная безопасность", after=110)
center("ОТЧЕТ", bold=True, size=16)
center("по практической работе № 5", bold=True)
center("Дисциплина: «Клиент-серверные технологии и их безопасность»", after=6)
center("Тема: «Реализация ролевой модели разграничения доступа (RBAC)»")
center("Тема мини-проекта: «CI/CD Security Pipeline: настройка автоматического сканирования "
       "уязвимостей исходного кода (SAST) и зависимостей (SCA) в GitHub Actions / GitLab CI»", after=90)
for line in ("Руководитель, преподаватель _____________ Казиева Н.М.",
             "«___» __________________ 2026", "",
             "Выполнил магистрант группы МСИБ-24",
             "Нуртазинов Ислам Тулегенович",
             "«___» __________________ 2026"):
    para(line, WD_ALIGN_PARAGRAPH.RIGHT, indent=False)
center("", after=70)
center("Астана, 2026").runs[0].add_break(WD_BREAK.PAGE)

# ---------- 1 ----------
doc.add_heading("1. Цель и задачи работы", 1)
para("Цель работы — реализовать ролевую модель разграничения доступа (RBAC) в клиент-серверном "
     "приложении и настроить для него пайплайн CI/CD, который при каждом изменении кода автоматически "
     "проверяет исходный код (SAST) и зависимости (SCA) на уязвимости.")
para("Задачи:")
bullets([
    "спроектировать базу данных RBAC: пользователи, роли, разрешения и связи между ними;",
    "реализовать REST API на FastAPI с тремя ресурсами разного уровня доступа;",
    "настроить в GitHub Actions автоматический запуск SAST, SCA и тестов ролевой модели, "
    "подготовить такой же пайплайн для GitLab CI;",
    "показать работу пайплайна на версии с уязвимостями и на исправленной версии;",
    "провести негативное тестирование ролевой модели (тесты 1–3, IDOR, эскалация привилегий).",
])

# ---------- 2 ----------
doc.add_heading("2. Краткие теоретические сведения", 1)
para("RBAC (Role-Based Access Control) — модель, в которой права назначаются не пользователям напрямую, "
     "а ролям. Пользователь получает одну или несколько ролей, роль объединяет набор разрешений, "
     "а разрешение описывает действие над ресурсом. Чтобы изменить права сотрудника, достаточно "
     "сменить его роль. Модель опирается на принцип наименьших привилегий (PoLP): каждой роли выдаются "
     "только те разрешения, которые нужны для её задач.")
para("SAST (Static Application Security Testing) — анализ исходного кода без его запуска. Инструмент "
     "ищет в коде опасные конструкции: SQL-запросы, собранные из строк, слабые алгоритмы хеширования, "
     "секреты в тексте программы. В работе использован Bandit — анализатор для Python.")
para("SCA (Software Composition Analysis) — проверка сторонних библиотек. Инструмент сравнивает версии "
     "зависимостей с базами известных уязвимостей. В работе использован pip-audit, который проверяет "
     "файл requirements.txt по базам PyPI Advisory Database и OSV, включая транзитивные зависимости.")
para("Если эти проверки встроены в пайплайн CI/CD, они выполняются при каждом push и pull request. "
     "Уязвимость обнаруживается до слияния изменения в основную ветку, а не после выпуска "
     "(подход «shift-left»).")
table("Сравнение SAST и SCA",
      ["", "SAST", "SCA"],
      [["Что проверяется", "Собственный исходный код", "Сторонние библиотеки (зависимости)"],
       ["Что находит", "Ошибки в коде: инъекции, слабая криптография, секреты",
        "Известные уязвимости (CVE) в используемых версиях"],
       ["Инструмент в работе", "Bandit", "pip-audit"],
       ["Способ исправления", "Изменить код", "Обновить версию библиотеки"]],
      [3.8, 6.2, 6.2])

# ---------- 3 ----------
doc.add_heading("3. Проектирование базы данных RBAC", 1)
para("База данных состоит из пяти таблиц. Таблицы users, roles и permissions хранят пользователей, "
     "роли и разрешения. Таблицы user_roles и role_permissions реализуют связи «многие-ко-многим». "
     "Внешние ключи объявлены с ON DELETE CASCADE и ON UPDATE CASCADE: при удалении пользователя "
     "или роли связанные записи удаляются автоматически.")
figure("er.png", "ER-диаграмма базы данных RBAC")
schema = read("sql/rbac_schema.sql")
listing(schema[schema.index("CREATE TABLE users"):schema.index("-- Начальные данные")].strip(),
        "SQL-скрипт создания таблиц (sql/rbac_schema.sql, PostgreSQL)")
para("Демонстрационный сервис использует ту же схему в SQLite, чтобы запускаться без установки СУБД. "
     "Скрипт для PostgreSQL находится в файле sql/rbac_schema.sql.")
table("Матрица «роль — разрешения»",
      ["Роль", "VIEW_PUBLIC", "VIEW_AUDIT", "MANAGE_USERS"],
      [["USER", "да", "—", "—"], ["MODERATOR", "да", "да", "—"], ["ADMIN", "да", "да", "да"]],
      [4, 4, 4, 4])

# ---------- 4 ----------
doc.add_heading("4. Реализация сервиса и проверки прав", 1)
para("Сервис написан на Python (FastAPI) и состоит из трёх файлов: app/database.py — работа с БД, "
     "app/auth.py — аутентификация и проверка прав, app/main.py — эндпоинты. После входа пользователь "
     "получает JWT-токен, в котором записан только его идентификатор. Роли и разрешения при каждом "
     "запросе читаются из базы данных.")
table("Эндпоинты сервиса",
      ["Метод и путь", "Кому доступно", "Проверка"],
      [["POST /api/v1/login", "Всем", "Логин и пароль"],
       ["GET /api/v1/public", "Всем авторизованным", "Действительный токен"],
       ["GET /api/v1/moderator/audit", "MODERATOR, ADMIN", "require_role"],
       ["GET, POST /api/v1/admin/users", "ADMIN с правом MANAGE_USERS", "require_role + check_permission"],
       ["PUT /api/v1/admin/users/{id}/role", "ADMIN с правом MANAGE_USERS", "require_role + check_permission"],
       ["GET /api/v1/users/{id}", "Владелец профиля или MANAGE_USERS", "Сравнение id с id из токена"]],
      [6.2, 5.2, 4.8])
para("Проверка прав реализована как зависимости FastAPI (аналог middleware). Функция get_current_user "
     "проверяет токен и возвращает ошибку 401, если он отсутствует или недействителен. Функции "
     "require_role и check_permission читают роли и разрешения пользователя из БД и возвращают 403, "
     "если прав недостаточно.")
listing(source("app/auth.py", "get_current_user", "require_role", "check_permission"),
        "Проверка токена, ролей и разрешений (app/auth.py)")
listing(source("app/main.py", "audit", "list_users", "create_user", "profile"),
        "Защищённые эндпоинты (app/main.py)")

# ---------- 5 ----------
doc.add_heading("5. Пайплайн безопасности CI/CD", 1)
para("Пайплайн описан в файле .github/workflows/security.yml и запускается при каждом push в ветку main "
     "и при каждом pull request. Он состоит из трёх независимых заданий, которые выполняются параллельно.")
figure("pipeline.png", "Схема пайплайна безопасности")
bullets([
    "SAST (Bandit): команда bandit -r app -ll проверяет каталог app. Задание завершается ошибкой, "
    "если найдены проблемы уровня MEDIUM или HIGH.",
    "SCA (pip-audit): команда pip-audit -r requirements.txt проверяет зависимости. Задание завершается "
    "ошибкой, если хотя бы у одной библиотеки есть известная уязвимость.",
    "Тесты RBAC (pytest): 8 тестов проверяют, что каждая роль получает доступ только к своим ресурсам.",
])
para("Если хотя бы одно задание завершилось ошибкой, запуск помечается как неуспешный. При включённой "
     "защите ветки (Settings → Branches → Require status checks to pass) такое изменение нельзя слить в main.")
listing(read(".github/workflows/security.yml"), "Пайплайн GitHub Actions (.github/workflows/security.yml)")
para("Для GitLab CI подготовлен файл .gitlab-ci.yml с теми же тремя заданиями и теми же командами. "
     "Отличается только синтаксис: в GitLab задания объединяются в стадии (stages) и выполняются "
     "в контейнере python:3.12-slim.")
listing(read(".gitlab-ci.yml"), "Пайплайн GitLab CI (.gitlab-ci.yml)")

# ---------- 6 ----------
doc.add_heading("6. Результаты сканирования", 1)
doc.add_heading("6.1. Исходная версия с уязвимостями", 2)
audit = read("reports/before/pip-audit.txt")
rows = [line.split() for line in audit.splitlines() if re.match(r"^(pyjwt|starlette|fastapi)\s", line)]
unique = {(r[0], r[2]) for r in rows}
by_package = {name: len({r[2] for r in rows if r[0] == name}) for name in ("pyjwt", "starlette")}
para("Первый коммит репозитория содержит версию сервиса с намеренно оставленными уязвимостями. "
     "Bandit нашёл в ней две блокирующие проблемы: хеширование паролей алгоритмом MD5 (уровень High) "
     "и SQL-запрос, собранный из строки (уровень Medium).")
figure("bandit_before.png", "Результат SAST (Bandit) для исходной версии", 15.5)
para(f"pip-audit нашёл уязвимости в двух пакетах: PyJWT 2.3.0 и starlette 0.37.2. Всего записей "
     f"в отчёте — {len(rows)}, уникальных идентификаторов уязвимостей — {len(unique)} "
     f"(PyJWT — {by_package['pyjwt']}, starlette — {by_package['starlette']}). "
     "Пакет starlette не указан в requirements.txt: это транзитивная зависимость, которую "
     "устанавливает fastapi 0.112.0.")
figure("pip_audit_before.png", "Результат SCA (pip-audit) для исходной версии (начало вывода)", 11.5)
para("Обе команды завершились с кодом 1, поэтому задания SAST и SCA в пайплайне завершаются ошибкой.")

doc.add_heading("6.2. Устранение уязвимостей", 2)
table("Найденные уязвимости и исправления",
      ["Находка", "Было", "Стало"],
      [["B324, High: слабый хеш паролей (app/auth.py)",
        "hashlib.md5(password.encode()).hexdigest()",
        "PBKDF2-HMAC-SHA256, 200 000 итераций, случайная соль для каждого пароля"],
       ["B608, Medium: SQL-инъекция (app/database.py)",
        "f\"SELECT * FROM users WHERE username = '{username}'\"",
        "Параметризованный запрос: \"... WHERE username = ?\", (username,)"],
       ["B105, Low: секрет подписи JWT в коде (app/auth.py)",
        "SECRET_KEY = \"supersecret123\"",
        "Секрет из переменной окружения JWT_SECRET; если она не задана — случайный при запуске"],
       ["SCA: уязвимые версии библиотек (requirements.txt)",
        "fastapi 0.112.0, PyJWT 2.3.0, uvicorn 0.30.0",
        "fastapi 0.162.2, PyJWT 2.15.1, uvicorn 0.54.0 (starlette обновляется до 1.7.0)"]],
      [4.6, 5.6, 6])
para("Находка B105 имеет уровень Low и не блокирует пайплайн, но секрет в исходном коде позволяет "
     "любому, кто видит репозиторий, подделать токен администратора, поэтому она тоже исправлена.")

doc.add_heading("6.3. Повторное сканирование", 2)
para("После исправлений Bandit не находит проблем уровня Medium и High, pip-audit не находит известных "
     "уязвимостей, все 8 тестов проходят. Обе команды завершаются с кодом 0.")
figure("bandit_after.png", "Результат SAST (Bandit) после исправлений", 13)
figure("pip_audit_after.png", "Результат SCA (pip-audit) после исправлений", 11)
figure("pytest_after.png", "Тесты ролевой модели после исправлений", 14)
para("В итогах Bandit осталась одна находка уровня Low: строка \"bearer\" в ответе /login принята "
     "за пароль. Это ложное срабатывание: значение — тип токена, а не секрет.")

if (IMG / "gh_fail.png").exists() and (IMG / "gh_ok.png").exists():
    doc.add_heading("6.4. Запуск в GitHub Actions", 2)
    para("Репозиторий размещён на GitHub: https://github.com/is1am/cicd-security-pipeline-v2. "
         "Запуск пайплайна для первого коммита завершился ошибкой: задания SAST и SCA не прошли, "
         "тесты прошли. Запуск для коммита с исправлениями завершился успешно, прошли все три задания.")
    figure("gh_fail.png", "GitHub Actions: запуск для исходной версии", 16)
    figure("gh_ok.png", "GitHub Actions: запуск после исправлений", 16)

# ---------- 7 ----------
doc.add_heading("7. Тестирование ролевой модели (Negative Testing)", 1)
para("Тесты 1–3 выполнены в Postman: запросы отправлялись сервису, запущенному локально "
     "(http://127.0.0.1:8010). Те же запросы собраны в коллекции "
     "postman/RBAC_PR5.postman_collection.json и повторяются автоматическими тестами в пайплайне.")
doc.add_heading("7.1. Тест 1 (позитивный)", 2)
para("Администратор входит в систему и получает токен, затем создаёт нового пользователя ivanov "
     "с ролью USER. Сервис возвращает 201 Created.")
figure("postman/login.png", "Вход администратора: сервис выдаёт JWT-токен", 15.5)
figure("postman/t1.png", "Тест 1: администратор создаёт пользователя, ответ 201 Created", 15.5)
doc.add_heading("7.2. Тест 2 (негативный)", 2)
para("Рядовой сотрудник (роль USER) обращается к административному эндпоинту /api/v1/admin/users "
     "со своим токеном. Запрос отклонён с кодом 403 Forbidden.")
figure("postman/t2.png", "Тест 2: пользователю с ролью USER отказано, ответ 403 Forbidden", 15.5)
doc.add_heading("7.3. Тест 3 (смена роли «на лету»)", 2)
para("Пользователь получает токен с ролью USER, затем администратор меняет его роль в базе данных. "
     "Токен не перевыпускается. Новые права действуют со следующего запроса, задержки нет: в токене "
     "хранится только идентификатор пользователя, а роли читаются из БД при каждом запросе. "
     "Отзыв роли применяется так же быстро.")
figure("postman/t3_1.png", "Тест 3, шаг 1: с ролью USER аудит недоступен, ответ 403", 15.5)
figure("postman/t3_2.png", "Тест 3, шаг 2: администратор назначает роль MODERATOR", 15.5)
figure("postman/t3_3.png", "Тест 3, шаг 3: тот же токен, доступ к аудиту появился, ответ 200", 15.5)
para("Если бы роли записывались в сам токен, изменение роли начинало бы действовать только после "
     "истечения срока токена (здесь — до одного часа), и уволенный или пониженный в правах сотрудник "
     "сохранял бы доступ всё это время. Цена выбранного решения — дополнительный запрос к БД "
     "на каждое обращение.")
doc.add_heading("7.4. Эскалация привилегий и IDOR", 2)
para("Проверены две типовые атаки на неправильно настроенный RBAC: пользователь пытается сам назначить "
     "себе роль ADMIN и подставляет в адрес запроса чужой идентификатор. Обе попытки отклонены "
     "с кодом 403, собственный профиль пользователю доступен. Запросы выполнены скриптом "
     "scripts/api_demo.py, на рисунке — его вывод.")
figure("api_attacks.png", "Попытки эскалации привилегий и IDOR", 13.5)

# ---------- 8 ----------
doc.add_heading("8. Выводы", 1)
para("В работе спроектирована база данных RBAC из пяти таблиц и реализован сервис на FastAPI с тремя "
     "уровнями доступа. Негативные тесты показали, что пользователь с ролью USER не может открыть "
     "административные эндпоинты, назначить себе роль или прочитать чужой профиль, а смена роли "
     "в базе данных действует сразу.")
para("Правильно спроектированный RBAC предотвращает эскалацию привилегий за счёт нескольких решений. "
     "Права проверяются на сервере при каждом запросе и не зависят от того, что показывает клиент. "
     "Роли и разрешения хранятся в базе данных, а не в токене, поэтому пользователь не может изменить "
     "их сам, а отзыв прав действует немедленно. Каждой роли выданы только необходимые разрешения, "
     "а менять роли может только обладатель права MANAGE_USERS. Доступ к объекту проверяется "
     "по идентификатору из токена, а не из адреса запроса, что закрывает IDOR.")
para("Пайплайн CI/CD дополняет ролевую модель: он проверяет каждое изменение кода. В исходной версии "
     f"Bandit нашёл слабый хеш паролей и SQL-инъекцию, pip-audit — уязвимости в двух библиотеках "
     f"(уникальных идентификаторов — {len(unique)}). Обе проблемы в коде позволяли обойти ролевую модель: через SQL-инъекцию или подбор "
     "MD5-хешей можно получить учётную запись администратора при корректно настроенных ролях. "
     "После исправлений пайплайн проходит полностью. Тесты ролевой модели в пайплайне не дают случайно "
     "ослабить проверку прав при дальнейших изменениях.")

out = ROOT / "Отчет_ПР5.docx"
doc.save(out)
print("Сохранено:", out.name, "| рисунков:", counters["рис"], "| таблиц:", counters["табл"],
      "| листингов:", counters["лист"])
