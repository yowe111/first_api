"""
main.py — ГЛАВНЫЙ ФАЙЛ (ТОЧКА ВХОДА).

Именно этот файл «собирает» приложение воедино:
- создаёт объект FastAPI (это и есть наше приложение);
- подключает роутеры (группы эндпоинтов);
- описывает главную страницу.

Команда запуска `uvicorn src.main:app` читается так:
«запусти сервер uvicorn, возьми объект `app` из файла src/main.py».
"""

# asynccontextmanager — превращает функцию в «менеджер контекста»,
# который умеет выполнять код ДО и ПОСЛЕ работы приложения (см. lifespan ниже).
from contextlib import asynccontextmanager

# FastAPI — сам класс приложения.
from fastapi import FastAPI
# HTMLResponse — тип ответа, чтобы вернуть HTML-страницу, а не JSON.
from fastapi.responses import HTMLResponse

# init_db — создаёт таблицы в базе при старте.
from src.database import init_db
# Импортируем наши роутеры (файлы с эндпоинтами).
from src.routers import auth, users


# Функция управления «жизненным циклом» приложения.
# Декоратор @asynccontextmanager позволяет разделить её на две части:
# то, что до `yield`, выполняется ПРИ СТАРТЕ, а то, что после — ПРИ ОСТАНОВКЕ.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Выполняется при старте приложения ---
    await init_db()   # создаём таблицы в базе, если их ещё нет
    yield             # здесь приложение «живёт» и обрабатывает запросы
    # --- Выполняется при остановке приложения ---
    # (сюда можно добавить закрытие соединений и т.п. — пока не требуется)


# Создаём приложение. Аргументы title/description/version попадают в /docs.
# lifespan=lifespan — подключаем функцию выше, чтобы при старте создались таблицы.
app = FastAPI(
    title="My API",
    description="Учебное приложение: Hello World + базовая авторизация",
    version="0.1.0",
    lifespan=lifespan,
)

# Подключаем роутеры к приложению. После этого станут доступны их адреса
# (/auth/register, /auth/login, /users/me).
app.include_router(auth.router)
app.include_router(users.router)


# Эндпоинт главной страницы. Декоратор говорит:
# «GET-запрос на / (корень сайта) обрабатывает функция index».
# response_class=HTMLResponse — вернём HTML (веб-страницу), а не JSON.
@app.get("/", response_class=HTMLResponse, tags=["Главная"])
async def index() -> str:
    """Главная страница. Адрес: http://localhost:8000/"""
    # Возвращаем строку с HTML-разметкой. Тройные кавычки позволяют
    # писать многострочный текст.
    return """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="utf-8">
        <title>My API</title>
        <style>
            body { font-family: sans-serif; text-align: center; margin-top: 80px; }
            h1 { font-size: 48px; }
            a { color: #2563eb; }
        </style>
    </head>
    <body>
        <h1>Hello World</h1>
        <p>Это учебное приложение на FastAPI.</p>
        <p>
            Открой <a href="/docs">/docs</a> — там интерактивная документация,
            где можно протестировать регистрацию и вход.
        </p>
    </body>
    </html>
    """


# Ещё один простой эндпоинт — возвращает JSON (а не HTML).
# `-> dict[str, str]` подсказывает: функция вернёт словарь строка->строка.
# FastAPI сам превратит словарь в JSON-ответ.
@app.get("/hello", tags=["Главная"])
async def hello() -> dict[str, str]:
    """Простой JSON-ответ. Адрес: http://localhost:8000/hello"""
    return {"message": "Hello World"}
