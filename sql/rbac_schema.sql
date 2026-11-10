-- ПР5. Схема базы данных RBAC (PostgreSQL)
-- Запуск: psql -U postgres -d rbac -f sql/rbac_schema.sql

CREATE TABLE users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TABLE roles (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE permissions (
    id       SERIAL PRIMARY KEY,
    name     VARCHAR(50) NOT NULL UNIQUE,
    resource VARCHAR(50) NOT NULL,
    action   VARCHAR(20) NOT NULL
);

-- Связь многие-ко-многим: пользователь <-> роль
CREATE TABLE user_roles (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE,
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE ON UPDATE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- Связь многие-ко-многим: роль <-> разрешение
CREATE TABLE role_permissions (
    role_id       INTEGER NOT NULL REFERENCES roles(id)       ON DELETE CASCADE ON UPDATE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(id) ON DELETE CASCADE ON UPDATE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- Начальные данные
INSERT INTO roles (name, description) VALUES
    ('ADMIN',     'Администратор'),
    ('MODERATOR', 'Модератор'),
    ('USER',      'Рядовой сотрудник');

INSERT INTO permissions (name, resource, action) VALUES
    ('VIEW_PUBLIC',  'public', 'read'),
    ('VIEW_AUDIT',   'audit',  'read'),
    ('MANAGE_USERS', 'users',  'manage');

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r
JOIN permissions p ON
       (r.name = 'ADMIN')
    OR (r.name = 'MODERATOR' AND p.name IN ('VIEW_PUBLIC', 'VIEW_AUDIT'))
    OR (r.name = 'USER'      AND p.name = 'VIEW_PUBLIC');
