"""Работа с базой данных RBAC (SQLite, пять таблиц)."""
import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", "rbac.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    is_active     INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS roles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    description TEXT
);
CREATE TABLE IF NOT EXISTS permissions (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    name     TEXT NOT NULL UNIQUE,
    resource TEXT NOT NULL,
    action   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE ON UPDATE CASCADE,
    PRIMARY KEY (user_id, role_id)
);
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id       INTEGER NOT NULL REFERENCES roles(id)       ON DELETE CASCADE ON UPDATE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE ON UPDATE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);
"""

# Начальные данные: роли, разрешения и матрица «роль — разрешения»
ROLES = [
    ("ADMIN", "Администратор"),
    ("MODERATOR", "Модератор"),
    ("USER", "Рядовой сотрудник"),
]
PERMISSIONS = [
    ("VIEW_PUBLIC", "public", "read"),
    ("VIEW_AUDIT", "audit", "read"),
    ("MANAGE_USERS", "users", "manage"),
]
ROLE_PERMISSIONS = {
    "ADMIN": ["VIEW_PUBLIC", "VIEW_AUDIT", "MANAGE_USERS"],
    "MODERATOR": ["VIEW_PUBLIC", "VIEW_AUDIT"],
    "USER": ["VIEW_PUBLIC"],
}


def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # без этого SQLite не проверяет FOREIGN KEY
    return conn


def query(sql, params=()):
    """SELECT: возвращает список строк."""
    conn = connect()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def execute(sql, params=()):
    """INSERT / UPDATE / DELETE: возвращает id добавленной строки."""
    conn = connect()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def create_tables():
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        for name, description in ROLES:
            conn.execute("INSERT OR IGNORE INTO roles (name, description) VALUES (?, ?)",
                         (name, description))
        for name, resource, action in PERMISSIONS:
            conn.execute("INSERT OR IGNORE INTO permissions (name, resource, action) VALUES (?, ?, ?)",
                         (name, resource, action))
        for role, permissions in ROLE_PERMISSIONS.items():
            for permission in permissions:
                conn.execute(
                    "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) "
                    "SELECT r.id, p.id FROM roles r, permissions p WHERE r.name = ? AND p.name = ?",
                    (role, permission))
        conn.commit()
    finally:
        conn.close()


def find_user(username):
    rows = query("SELECT * FROM users WHERE username = ?", (username,))
    return rows[0] if rows else None


def get_user(user_id):
    rows = query("SELECT * FROM users WHERE id = ?", (user_id,))
    return rows[0] if rows else None


def get_roles(user_id):
    rows = query("SELECT r.name FROM roles r JOIN user_roles ur ON ur.role_id = r.id "
                 "WHERE ur.user_id = ?", (user_id,))
    return {row["name"] for row in rows}


def get_permissions(user_id):
    rows = query("SELECT DISTINCT p.name FROM permissions p "
                 "JOIN role_permissions rp ON rp.permission_id = p.id "
                 "JOIN user_roles ur ON ur.role_id = rp.role_id "
                 "WHERE ur.user_id = ?", (user_id,))
    return {row["name"] for row in rows}


def create_user(username, password_hash, role):
    user_id = execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                      (username, password_hash))
    set_role(user_id, role)
    return user_id


def set_role(user_id, role):
    """Заменяет роль пользователя на указанную."""
    execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))
    execute("INSERT INTO user_roles (user_id, role_id) SELECT ?, id FROM roles WHERE name = ?",
            (user_id, role))


def list_users():
    rows = query("SELECT id, username, is_active FROM users ORDER BY id")
    return [{"id": row["id"], "username": row["username"], "is_active": bool(row["is_active"]),
             "roles": sorted(get_roles(row["id"]))} for row in rows]
