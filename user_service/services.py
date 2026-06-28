import uuid
import asyncio
import bcrypt
from redis.asyncio import Redis


async def hash_password(password: str) -> str:
    """Асинхронно хеширует пароль."""
    # bcrypt.hashpw — синхронный, выполняем в потоке
    return await asyncio.to_thread(
        lambda: bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    )


async def verify_password(password: str, hashed: str) -> bool:
    """Асинхронно проверяет пароль."""
    return await asyncio.to_thread(
        lambda: bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    )


async def register_user(redis: Redis, email: str, password: str) -> str:
    """Создаёт пользователя, возвращает user_id."""
    # Проверка уникальности email
    if await redis.exists(f"email:{email}"):
        raise ValueError("Email already registered")

    user_id = str(uuid.uuid4())
    hashed = await hash_password(password)

    # Сохраняем данные
    await redis.hset(f"user:{user_id}", mapping={
        "email": email,
        "password": hashed
    })
    await redis.set(f"email:{email}", user_id)
    return user_id


async def authenticate_user(redis: Redis, email: str, password: str) -> str:
    """Возвращает user_id при успехе, иначе выбрасывает ValueError."""
    user_id = await redis.get(f"email:{email}")
    if not user_id:
        raise ValueError("Invalid email or password")

    stored_password = await redis.hget(f"user:{user_id}", "password")
    if not stored_password or not await verify_password(password, stored_password):
        raise ValueError("Invalid email or password")

    return user_id


async def get_user(redis: Redis, user_id: str) -> dict | None:
    """Возвращает словарь с email или None."""
    data = await redis.hgetall(f"user:{user_id}")
    if not data:
        return None
    return {"user_id": user_id, "email": data["email"]}