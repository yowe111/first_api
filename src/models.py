"""
models.py — МОДЕЛИ (ТАБЛИЦЫ БАЗЫ ДАННЫХ).

Модель — это Python-класс, который SQLAlchemy превращает в таблицу в базе.
Правило простое:
    класс      = таблица
    атрибут    = колонка (столбец) таблицы
    объект     = одна строка таблицы

Здесь описана одна модель — User (пользователь).
"""

# datetime — встроенный тип Python для даты и времени.
# Используем его как тип для поля created_at.
from datetime import datetime

# Импортируем из SQLAlchemy:
# - TIMESTAMP: тип колонки «дата и время» в базе;
# - String: тип колонки «строка» (можно ограничить длину);
# - func: доступ к функциям базы данных (например, func.now() = «текущее время»).
from sqlalchemy import TIMESTAMP, String, func

# Инструменты для описания колонок в новом стиле SQLAlchemy 2.0:
# - Mapped: подсказка типа для поля-колонки;
# - mapped_column: сама настройка колонки (первичный ключ, длина и т.п.).
from sqlalchemy.orm import Mapped, mapped_column

# Base — общий предок всех моделей (мы создали его в database.py).
from src.database import Base


# Класс User наследуется от Base, поэтому SQLAlchemy будет считать его таблицей.
class User(Base):
    """Модель пользователя = таблица `users` в базе данных."""

    # Служебное поле: задаёт имя таблицы в базе.
    __tablename__ = "users"

    # ── Колонки таблицы ───────────────────────────────────────────────

    # id — уникальный номер записи.
    # Mapped[int] — тип значения (целое число).
    # primary_key=True — это «первичный ключ»: главный идентификатор строки.
    # База сама выдаёт новый id при добавлении пользователя (1, 2, 3, ...).
    id: Mapped[int] = mapped_column(primary_key=True)

    # username — имя пользователя (логин).
    # String(64) — строка длиной до 64 символов.
    # unique=True — двух одинаковых логинов быть не может.
    # index=True — построить индекс, чтобы поиск по логину был быстрым.
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)

    # hashed_password — ХЕШ пароля (зашифрованный «отпечаток»), а НЕ сам пароль.
    # Настоящий пароль в базе не хранится никогда — так безопаснее.
    hashed_password: Mapped[str] = mapped_column(String(255))

    # created_at — когда была создана запись.
    # Mapped[datetime] — тип «дата и время».
    # server_default=func.now() — при добавлении строки БАЗА сама подставит
    # текущее время, нам не нужно указывать его вручную.
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )
