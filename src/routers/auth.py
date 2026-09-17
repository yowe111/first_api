"""
routers/auth.py — ЭНДПОИНТЫ АВТОРИЗАЦИИ.

«Роутер» (APIRouter) — это группа связанных адресов (эндпоинтов).
Здесь два адреса:
- POST /auth/register — создать нового пользователя;
- POST /auth/login    — войти и получить токен.

Слово «эндпоинт» = конкретный адрес API + функция, которая его обрабатывает.
Слово «POST» = тип HTTP-запроса, которым обычно ОТПРАВЛЯЮТ данные на сервер.
"""

from typing import Annotated

# APIRouter — создаёт группу эндпоинтов.
# Depends — подключение зависимостей; HTTPException — вернуть ошибку;
# status — понятные коды ответов.
from fastapi import APIRouter, Depends, HTTPException, status

# OAuth2PasswordRequestForm — готовая «форма входа»: FastAPI сам достанет
# из запроса поля username и password (они приходят как данные формы).
from fastapi.security import OAuth2PasswordRequestForm

# select — построение запроса «выбрать...» к базе.
from sqlalchemy import select
# AsyncSession — тип асинхронной сессии (для подсказки типа).
from sqlalchemy.ext.asyncio import AsyncSession

# Наши модули:
from src.database import get_session   # зависимость: сессия базы
from src.models import User            # модель-таблица пользователя
from src.schemas import Token, UserCreate, UserRead  # схемы данных
from src.security import (             # функции безопасности
    create_access_token,
    hash_password,
    verify_password,
)

# Создаём роутер.
# prefix="/auth" — все адреса ниже начинаются с /auth (получится /auth/register).
# tags=["Авторизация"] — группировка на странице документации /docs.
router = APIRouter(prefix="/auth", tags=["Авторизация"])


# @router.post(...) — ДЕКОРАТОР. Он «привязывает» функцию ниже к адресу.
# Читается так: «когда придёт POST-запрос на /auth/register — вызови register».
# response_model=UserRead — ответ будет иметь форму схемы UserRead (без пароля).
# status_code=201 — код «успешно создано».
@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    # data — тело запроса; FastAPI проверит его по схеме UserCreate.
    data: UserCreate,
    # session — сессия базы; FastAPI подставит её через зависимость.
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Регистрация нового пользователя."""
    # Сначала проверяем, не занят ли уже такой логин.
    result = await session.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none() is not None:
        # Логин занят — возвращаем ошибку 400 «неверный запрос».
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует",
        )

    # Создаём объект пользователя. Пароль СРАЗУ хешируем — открытый не храним.
    user = User(
        username=data.username,
        hashed_password=hash_password(data.password),
    )
    session.add(user)          # добавляем объект в сессию (пока только в памяти)
    await session.commit()     # commit — «сохранить изменения» в базу по-настоящему
    await session.refresh(user)  # перечитываем объект, чтобы получить id и created_at
    return user                # FastAPI превратит его в JSON по схеме UserRead


# Эндпоинт входа: POST /auth/login. В ответе — токен (схема Token).
@router.post("/login", response_model=Token)
async def login(
    # form — данные формы входа. Depends() без аргумента означает:
    # «создай OAuth2PasswordRequestForm из запроса». Внутри будут form.username
    # и form.password.
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """Вход в систему: проверяем логин/пароль и выдаём токен."""
    # Ищем пользователя по введённому логину.
    result = await session.execute(select(User).where(User.username == form.username))
    user = result.scalar_one_or_none()

    # Проверяем сразу два условия:
    # 1) пользователь найден (user is not None);
    # 2) пароль верный (verify_password вернул True).
    # Если хоть что-то не так — даём ОДИНАКОВУЮ ошибку, чтобы не подсказывать,
    # логин неправильный или пароль.
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
        )

    # Логин и пароль верны — создаём токен и возвращаем его клиенту.
    token = create_access_token(subject=user.username)
    return Token(access_token=token)
