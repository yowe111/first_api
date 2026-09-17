"""
security.py — БЕЗОПАСНОСТЬ: ПАРОЛИ И ТОКЕНЫ.

Две задачи:
1) Хранить пароли безопасно. Мы НЕ храним пароль как есть.
   Вместо этого храним его «хеш» — необратимый отпечаток (bcrypt).
2) Выдавать «пропуск» после входа. Это токен JWT: клиент показывает его
   при каждом обращении к защищённым эндпоинтам, и сервер понимает, кто это.

Аналогия:
- Хеш пароля — как отпечаток пальца: по нему можно ПРОВЕРИТЬ человека,
  но нельзя «восстановить» самого человека.
- JWT-токен — как браслет на входе в клуб: получил при входе, показываешь
  охране, и тебя пускают, не спрашивая паспорт заново.
"""

# Инструменты для работы с датой/временем — нужны, чтобы задать
# срок годности токена.
from datetime import datetime, timedelta, timezone

# bcrypt — библиотека для хеширования паролей.
import bcrypt

# jwt (библиотека PyJWT) — создание и проверка токенов JWT.
import jwt

# Наши настройки: там лежит секретный ключ и срок жизни токена.
from src.config import settings

# Алгоритм, которым подписывается токен. HS256 — распространённый выбор.
# «Подпись» гарантирует, что токен не подделали.
ALGORITHM = "HS256"


# Превращает обычный пароль в безопасный хеш для хранения в базе.
def hash_password(password: str) -> str:
    # password.encode() — строку превращаем в байты (bcrypt работает с байтами).
    # bcrypt.gensalt() — генерирует случайную «соль» (добавку), чтобы даже
    # одинаковые пароли давали разные хеши.
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    # .decode() — превращаем байты обратно в строку, чтобы сохранить в базе.
    return hashed.decode()


def verify_password(password: str, hashed: str) -> bool:
    # bcrypt сам «пересчитает» введённый пароль с той же солью и сравнит.
    return bcrypt.checkpw(password.encode(), hashed.encode())


# Создаёт новый токен доступа для пользователя.
# subject — это то, что мы «зашиваем» внутрь токена (у нас — логин).
def create_access_token(subject: str) -> str:
    # Считаем момент времени, когда токен «протухнет»:
    # текущее время (в UTC) + заданное число минут из настроек.
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    # payload — «начинка» токена (полезные данные):
    # "sub" (subject) — кому принадлежит токен;
    # "exp" (expire)  — до какого времени он действителен.
    payload = {"sub": subject, "exp": expire}
    # jwt.encode подписывает начинку секретным ключом и возвращает строку-токен.
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


# Проверяет токен и достаёт из него логин пользователя.
# Возвращает логин (str), если всё хорошо, или None, если токен плохой.
def decode_access_token(token: str) -> str | None:
    # Пробуем разобрать токен. Если он подделан или просрочен —
    # jwt.decode «бросит» ошибку, и мы попадём в блок except.
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        # .get("sub") достаёт логин из начинки; если его нет — вернётся None.
        return payload.get("sub")
    except jwt.PyJWTError:
        # Любая ошибка проверки токена (неверная подпись, истёк срок и т.д.).
        return None
