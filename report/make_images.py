"""Рисунки для отчёта: ER-диаграмма, схема пайплайна и снимки вывода инструментов.

Снимки консоли строятся из настоящих файлов в reports/ (вывод Bandit, pip-audit,
pytest и scripts/api_demo.py).  Запуск:  python report/make_images.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "report" / "img"
IMG.mkdir(parents=True, exist_ok=True)
FONTS = Path("C:/Windows/Fonts")


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


# ---------- снимок консоли ----------
def console(name, command, text, max_lines=None):
    lines = [line.rstrip().replace("\t", "    ") for line in text.strip("\n").splitlines()]
    if max_lines and len(lines) > max_lines:
        hidden = len(lines) - max_lines
        lines = lines[:max_lines] + [f"... (ещё {hidden} строк, полный вывод — в папке reports)"]
    mono, bold = font("consola.ttf", 17), font("consolab.ttf", 17)
    line_h, pad = 23, 18
    width = max(760, int(max(mono.getlength(s) for s in lines + ["> " + command])) + 2 * pad)
    height = pad * 2 + line_h * (len(lines) + 2)
    img = Image.new("RGB", (width, height), "#1e1e1e")
    draw = ImageDraw.Draw(img)
    draw.text((pad, pad), "> " + command, font=bold, fill="#9cdcfe")
    for i, line in enumerate(lines):
        low = line.lower()
        color = "#d4d4d4"
        if "403" in line or "severity: high" in low or "severity: medium" in low or low.startswith("found "):
            color = "#f48771"
        elif " 200 " in line or " 201 " in line or "passed" in low or "no issues" in low or "no known" in low:
            color = "#89d185"
        elif line.startswith(("Тест", "Шаг", "Эскалация", "Пользователь", "Свой")):
            color = "#dcdcaa"
        draw.text((pad, pad + line_h * (i + 2)), line, font=mono, fill=color)
    img.save(IMG / name)


def read(path):
    return (ROOT / path).read_text(encoding="utf-8", errors="replace")


def after(text, marker):
    """Часть вывода, начиная со строки с marker (служебный заголовок отбрасывается)."""
    return text[text.index(marker):]


console("bandit_before.png", "bandit -r app -ll", after(read("reports/before/bandit.txt"), "Test results"))
console("pip_audit_before.png", "pip-audit -r requirements.txt", read("reports/before/pip-audit.txt"), max_lines=16)
console("bandit_after.png", "bandit -r app -ll", after(read("reports/after/bandit.txt"), "Test results"))
console("pip_audit_after.png", "pip-audit -r requirements.txt", read("reports/after/pip-audit.txt"))
pytest_lines = [s for s in read("reports/after/pytest.txt").splitlines() if "::" in s or " passed" in s]
console("pytest_after.png", "pytest -v", "\n".join(pytest_lines))
for part in ("test1", "test2", "test3", "attacks"):
    console(f"api_{part}.png", "python scripts/api_demo.py", read(f"reports/api/{part}.txt"))


# ---------- ER-диаграмма ----------
def er_diagram():
    tables = [
        ("users", ["PK  id", "username", "password_hash", "is_active"]),
        ("user_roles", ["PK FK  user_id", "PK FK  role_id"]),
        ("roles", ["PK  id", "name", "description"]),
        ("role_permissions", ["PK FK  role_id", "PK FK  permission_id"]),
        ("permissions", ["PK  id", "name", "resource", "action"]),
    ]
    box_w, gap, row_h, head_h, top = 250, 70, 34, 42, 70
    width = 40 * 2 + box_w * 5 + gap * 4
    img = Image.new("RGB", (width, 330), "white")
    draw = ImageDraw.Draw(img)
    title, text, small = font("arialbd.ttf", 19), font("arial.ttf", 17), font("arialbd.ttf", 18)
    mid_y = top + head_h + row_h  # высота, на которой проходят линии связей
    for i, (name, fields) in enumerate(tables):
        x = 40 + i * (box_w + gap)
        height = head_h + row_h * len(fields) + 8
        link = name in ("user_roles", "role_permissions")
        draw.rectangle([x, top, x + box_w, top + height], outline="#1f3864", width=2,
                       fill="#f2f2f2" if link else "white")
        draw.rectangle([x, top, x + box_w, top + head_h], fill="#7f7f7f" if link else "#1f3864")
        draw.text((x + box_w / 2, top + head_h / 2), name, font=title, fill="white", anchor="mm")
        for j, field in enumerate(fields):
            draw.text((x + 12, top + head_h + 8 + row_h * j), field, font=text, fill="black")
        if i < 4:  # связь с соседней таблицей: «один» у справочника, «много» у таблицы связи
            x1, x2 = x + box_w, x + box_w + gap
            draw.line([x1, mid_y, x2, mid_y], fill="#1f3864", width=2)
            left, right = ("1", "N") if i % 2 == 0 else ("N", "1")
            draw.text((x1 + 8, mid_y - 24), left, font=small, fill="#c00000")
            draw.text((x2 - 8, mid_y - 24), right, font=small, fill="#c00000", anchor="ra")
    draw.text((40, 20), "Связи «многие-ко-многим» реализованы таблицами user_roles и role_permissions "
                        "(FOREIGN KEY, ON DELETE CASCADE)", font=text, fill="#404040")
    draw.text((40, 290), "PK — первичный ключ, FK — внешний ключ", font=text, fill="#404040")
    img.save(IMG / "er.png")


# ---------- схема пайплайна ----------
def pipeline_diagram():
    img = Image.new("RGB", (1500, 420), "white")
    draw = ImageDraw.Draw(img)
    head, text = font("arialbd.ttf", 20), font("arial.ttf", 17)

    def box(x, y, w, h, title, sub, fill):
        draw.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=fill, outline="#1f3864", width=2)
        draw.text((x + w / 2, y + h / 2 - (12 if sub else 0)), title, font=head, fill="#1f3864", anchor="mm")
        if sub:
            draw.text((x + w / 2, y + h / 2 + 16), sub, font=text, fill="#404040", anchor="mm")

    def arrow(x1, y1, x2, y2):
        draw.line([x1, y1, x2, y2], fill="#1f3864", width=3)
        draw.polygon([(x2, y2), (x2 - 14, y2 - 7), (x2 - 14, y2 + 7)], fill="#1f3864")

    box(30, 160, 230, 100, "push / pull request", "в ветку main", "#deeaf6")
    jobs = [("SAST: Bandit", "исходный код app/", 40),
            ("SCA: pip-audit", "requirements.txt", 160),
            ("Тесты: pytest", "ролевая модель", 280)]
    for title, sub, y in jobs:
        box(420, y, 330, 100, title, sub, "#fff2cc")
        arrow(260, 210, 420, y + 50)
        arrow(750, y + 50, 900, 210)
    box(900, 160, 250, 100, "Все задания", "успешны?", "#e2efda")
    arrow(1150, 190, 1250, 110)
    arrow(1150, 230, 1250, 310)
    box(1250, 60, 220, 100, "Да", "слияние разрешено", "#c6e0b4")
    box(1250, 260, 220, 100, "Нет", "изменение отклонено", "#f8cbad")
    img.save(IMG / "pipeline.png")


er_diagram()
pipeline_diagram()
print("Готово:", ", ".join(sorted(p.name for p in IMG.glob("*.png"))))
