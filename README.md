# My API — учебное FastAPI приложение

Небольшой проект, чтобы разобраться, как устроено современное веб-API на Python.
Внутри: **FastAPI**, **SQLAlchemy** (асинхронно) + **PostgreSQL**, **Poetry** и **Docker**.
Приложение запускается одной командой и умеет:

- показывать страницу «Hello World» на `http://localhost:8000/`;
- регистрировать пользователей и выдавать токен при входе (базовая авторизация);
- отдавать защищённый эндпоинт `/users/me`, доступный только с токеном.

---

## 1. Быстрый старт

Нужен только установленный **Docker Desktop**. Больше ничего ставить не надо
(ни Python, ни PostgreSQL) — всё поднимается внутри контейнеров.

```bash
# из папки my_api
docker compose up --build
```

Дождись строки вида `Application startup complete` и открой в браузере:

- `http://localhost:8000/` — страница **Hello World**;
- `http://localhost:8000/hello` — то же самое, но в виде JSON;
- `http://localhost:8000/docs` — **интерактивная документация** (Swagger UI),
  где можно нажимать кнопки и вызывать методы API прямо из браузера.

Остановить: `Ctrl+C`, затем при желании `docker compose down`.

> Если установлен `make`, можно короче: `make up`, `make logs`, `make down`.

---

## 2. Что такое каждая технология (простыми словами)

| Технология | Зачем нужна |
|------------|-------------|
| **FastAPI** | Фреймворк для создания API. Мы описываем «функции-обработчики», а он превращает их в веб-эндпоинты и сам делает документацию. |
| **Uvicorn** | Сервер, который запускает FastAPI-приложение и принимает HTTP-запросы. |
| **SQLAlchemy** | ORM: позволяет работать с таблицами базы как с обычными Python-классами, не писать SQL руками. |
| **PostgreSQL** | Сама база данных, где хранятся пользователи. |
| **asyncpg** | Драйвер, через который Python асинхронно общается с PostgreSQL. |
| **Pydantic** | Проверяет и описывает форму данных (что приходит и что уходит из API). |
| **Poetry** | Менеджер зависимостей: хранит список библиотек и ставит их. |
| **Docker / docker-compose** | Упаковывает приложение и базу в «контейнеры», чтобы всё запускалось одинаково на любой машине. |
| **JWT + bcrypt** | Авторизация: bcrypt безопасно хранит пароли, JWT выдаёт «пропуск» (токен) после входа. |

---

## 3. Структура проекта

```
my_api/
├── .env                  # настройки (логины/пароли БД, секретный ключ)
├── .gitignore            # что не коммитить в git
├── pyproject.toml        # список зависимостей (для Poetry)
├── app.dockerfile        # инструкция, как собрать образ приложения
├── docker-compose.yaml   # описание сервисов: app + postgres
├── Makefile              # короткие команды-ярлыки
├── README.md             # этот файл
└── src/                  # весь код приложения
    ├── __init__.py       # помечает src как Python-пакет
    ├── main.py           # точка входа: создаёт приложение, главная страница
    ├── config.py         # чтение настроек из .env
    ├── database.py       # подключение к БД, сессии, создание таблиц
    ├── models.py         # модели-таблицы (класс User)
    ├── schemas.py        # схемы Pydantic (форма входных/выходных данных)
    ├── security.py       # хеширование паролей и JWT-токены
    ├── dependencies.py   # проверка токена / получение текущего пользователя
    └── routers/          # группы эндпоинтов
        ├── __init__.py
        ├── auth.py       # /auth/register и /auth/login
        └── users.py      # /users/me (защищённый)
```

---

## 4. Как это всё работает вместе

### Что происходит при `docker compose up`

1. `docker-compose.yaml` поднимает **два контейнера**: `postgres` (база) и `app` (наше приложение).
2. Сначала запускается `postgres`. Docker ждёт (`healthcheck`), пока база будет готова.
3. Затем собирается и стартует `app` по инструкции из `app.dockerfile`:
   ставится Poetry, устанавливаются библиотеки из `pyproject.toml`, копируется код.
4. Запускается команда `uvicorn src.main:app` — сервер поднимает приложение из `src/main.py`.
5. При старте срабатывает `lifespan` → `init_db()` создаёт таблицы в базе (если их ещё нет).
6. Приложение слушает порт `8000`, который проброшен на `localhost:8000`.

### Путь одного запроса (на примере регистрации)

```
Клиент  →  POST /auth/register  →  router (auth.py)
                                     │
                    Pydantic (schemas.py) проверяет входные данные
                                     │
                    security.py хеширует пароль
                                     │
                    SQLAlchemy (models.py) сохраняет User в базу
                                     │
                    Pydantic (UserRead) формирует безопасный ответ (без пароля)
                                     ↓
Клиент  ←  JSON с id и username  ←──┘
```

---

## 5. Как проверить авторизацию

Удобнее всего через `http://localhost:8000/docs`.

**Шаг 1. Регистрация.** Открой `POST /auth/register`, нажми *Try it out* и отправь:

```json
{ "username": "alex", "password": "12345" }
```

В ответ придёт `id` и `username` нового пользователя.

**Шаг 2. Вход.** Нажми кнопку **Authorize** вверху страницы, введи тот же
`username` и `password`. Swagger сам вызовет `/auth/login`, получит токен и
подставит его во все запросы.

**Шаг 3. Защищённый эндпоинт.** Вызови `GET /users/me` — теперь он вернёт
твои данные. Без входа (без токена) он вернёт ошибку `401 Unauthorized`.

### То же самое через терминал (curl)

```bash
# Регистрация
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"alex\", \"password\": \"12345\"}"

# Вход — получаем токен (логин отправляется как форма!)
curl -X POST http://localhost:8000/auth/login \
  -d "username=alex&password=12345"

# Запрос к защищённому эндпоинту (подставь токен из предыдущего ответа)
curl http://localhost:8000/users/me \
  -H "Authorization: Bearer ВАШ_ТОКЕН"
```

---

## 6. Ключевые понятия, которые стоит запомнить

- **Модель ≠ Схема.** Модель (`models.py`) — это таблица в базе.
  Схема (`schemas.py`) — форма данных на входе/выходе API. Их разделяют,
  чтобы, например, не отдавать наружу хеш пароля.
- **Зависимости (Depends).** FastAPI умеет автоматически «подставлять» в
  обработчик нужные объекты: сессию базы (`get_session`) или текущего
  пользователя (`get_current_user`). Это и делает эндпоинт защищённым.
- **Асинхронность (`async`/`await`).** Позволяет серверу обслуживать много
  запросов одновременно, не блокируясь на ожидании ответа от базы.
- **Токен (JWT).** После входа клиент хранит токен и присылает его в заголовке
  `Authorization: Bearer <токен>`. Сервер по нему понимает, кто это, не спрашивая
  пароль каждый раз.

---

## 7. Полезные команды

```bash
docker compose up --build      # собрать и запустить
docker compose up --build -d   # то же, но в фоне
docker compose logs -f app     # смотреть логи приложения
docker compose ps -a           # статус контейнеров
docker compose down            # остановить и удалить контейнеры
docker compose down -v         # то же + удалить данные базы (чистый старт)
```

Зайти в базу вручную:

```bash
docker compose exec -it postgres psql -U myuser -d my_api
# внутри: \dt — список таблиц, SELECT * FROM users; — посмотреть пользователей
```

---

## 8. Что можно сделать дальше (идеи для практики)

1. Добавить поле `email` в модель `User` и схемы.
2. Сделать эндпоинт `GET /users` со списком всех пользователей (только для авторизованных).
3. Добавить роли (обычный пользователь / админ) и проверку прав.
4. Заменить создание таблиц через `init_db` на миграции (Alembic).
5. Написать тесты (pytest) для регистрации и входа.

---

## 9. Где что почитать (официальная документация)

Ссылки ведут на официальные сайты — это самый надёжный источник.
Рядом указано, какой файл проекта относится к теме.

| Технология | Файл в проекте | Документация |
|------------|----------------|--------------|
| **FastAPI** | `src/main.py`, `src/routers/*` | https://fastapi.tiangolo.com/ru/ (есть перевод на русский) |
| **Учебник FastAPI (по шагам)** | — | https://fastapi.tiangolo.com/ru/tutorial/ |
| **Pydantic** | `src/schemas.py` | https://docs.pydantic.dev/latest/ |
| **Pydantic Settings** | `src/config.py` | https://docs.pydantic.dev/latest/concepts/pydantic_settings/ |
| **SQLAlchemy (ORM)** | `src/models.py`, `src/database.py` | https://docs.sqlalchemy.org/en/20/orm/ |
| **SQLAlchemy async** | `src/database.py` | https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html |
| **PostgreSQL** | база данных | https://www.postgresql.org/docs/ |
| **Uvicorn** | запуск сервера | https://www.uvicorn.org/ |
| **Poetry** | `pyproject.toml` | https://python-poetry.org/docs/ |
| **Docker** | `app.dockerfile` | https://docs.docker.com/get-started/ |
| **Docker Compose** | `docker-compose.yaml` | https://docs.docker.com/compose/ |
| **PyJWT (токены)** | `src/security.py` | https://pyjwt.readthedocs.io/en/stable/ |
| **bcrypt (пароли)** | `src/security.py` | https://github.com/pyca/bcrypt/ |
| **JWT — что это** | `src/security.py` | https://jwt.io/introduction |

---

## 10. С чего начать изучение (пошаговый план)

Если ты только начинаешь, читай в таком порядке — от простого к сложному:

1. **Основы Python** (если ещё не уверен):
   официальный учебник — https://docs.python.org/3/tutorial/
   на русском (проект «Питонтьютор») — https://pythontutor.ru/

2. **Что такое HTTP и API** (запросы, методы GET/POST, коды ответов):
   https://developer.mozilla.org/ru/docs/Web/HTTP/Overview

3. **Учебник FastAPI** — самый важный шаг, проходи по порядку:
   https://fastapi.tiangolo.com/ru/tutorial/
   Особенно разделы: *First Steps*, *Path Parameters*, *Request Body*,
   *SQL (Relational) Databases*, *Security (OAuth2 + JWT)*.

4. **Асинхронность в Python** (что такое `async`/`await`):
   https://fastapi.tiangolo.com/ru/async/ (объяснено простыми словами)

5. **SQLAlchemy ORM** — как работать с таблицами через классы:
   https://docs.sqlalchemy.org/en/20/orm/quickstart.html

6. **Docker для новичков** — зачем нужны контейнеры:
   https://docs.docker.com/get-started/introduction/

### Порядок чтения кода этого проекта

Файлы удобнее изучать в такой последовательности (от простого к сложному):

`config.py` → `database.py` → `models.py` → `schemas.py` →
`security.py` → `dependencies.py` → `routers/auth.py` →
`routers/users.py` → `main.py`

Каждый файл снабжён подробными комментариями — читай их сверху вниз.

---

## 11. Частые вопросы (FAQ)

**Почему база называется `postgres` в строке подключения, а не `localhost`?**
Внутри Docker каждый сервис виден по своему имени из `docker-compose.yaml`.
Приложение и база — в одной сети, поэтому приложение обращается к базе
по имени сервиса `postgres`. С твоего компьютера та же база доступна по
`localhost` (порт задан в `.env` через `POSTGRES_PORT`).

**Где физически хранятся данные? Пропадут ли они после перезапуска?**
Данные лежат в Docker-томе `postgres_data` (см. `docker-compose.yaml`).
После `docker compose down` они сохраняются. Чтобы удалить их и начать
с чистой базы — используй `docker compose down -v`.

**Я изменил код — надо ли перезапускать?**
Сервер запущен с флагом `--reload`, поэтому при изменении Python-файлов
приложение перезапускается само. Если менял зависимости в `pyproject.toml`
или сам `Dockerfile` — нужна пересборка: `docker compose up --build`.

**Что такое `/docs` и `/redoc`?**
Это автоматически сгенерированная документация API.
`/docs` (Swagger UI) — интерактивная, можно нажимать кнопки и вызывать методы.
`/redoc` — тот же список эндпоинтов, но в виде красивой статичной странички.
