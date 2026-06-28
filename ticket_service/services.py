import uuid
import httpx
from redis.asyncio import Redis
from config import USER_SERVICE_URL

async def check_user_exists(http_client: httpx.AsyncClient, user_id: str) -> bool:
    """Проверяет существование пользователя через HTTP."""
    url = f"{USER_SERVICE_URL}/users/{user_id}"
    try:
        response = await http_client.get(url)
        return response.status_code == 200
    except httpx.RequestError:
        return False

async def create_ticket(redis: Redis, user_id: str) -> dict:
    """Создаёт билет с обратной связью и возвращает его данные."""
    ticket_id = str(uuid.uuid4())
    ticket_key = f"ticket:{ticket_id}"
    user_ticket_key = f"user:{user_id}:ticket"

    # Храним билет как хэш с user_id и статусом
    await redis.hset(ticket_key, mapping={"status": "active", "user_id": user_id})
    await redis.expire(ticket_key, 3600)
    # Обратная связь: user_id -> ticket_id
    await redis.setex(user_ticket_key, 3600, ticket_id)

    return {"ticket_id": ticket_id, "status": "active", "user_id": user_id}

async def delete_ticket(redis: Redis, ticket_id: str) -> bool:
    """Удаляет билет и обратную связь. Возвращает True, если билет существовал."""
    ticket_key = f"ticket:{ticket_id}"
    user_id = await redis.hget(ticket_key, "user_id")
    if not user_id:
        return False

    await redis.delete(ticket_key, f"user:{user_id}:ticket")
    return True

async def get_ticket_status(redis: Redis, ticket_id: str) -> dict | None:
    """Возвращает полную информацию о билете или None."""
    data = await redis.hgetall(f"ticket:{ticket_id}")
    if not data:
        return None
    return {
        "ticket_id": ticket_id,
        "status": data.get("status", "unknown"),
        "user_id": data.get("user_id", "")
    }

async def get_ticket_by_user(redis: Redis, user_id: str) -> dict | None:
    """Ищет активный билет по user_id."""
    ticket_id = await redis.get(f"user:{user_id}:ticket")
    if not ticket_id:
        return None
    # Проверим, что билет ещё жив
    if not await redis.exists(f"ticket:{ticket_id}"):
        await redis.delete(f"user:{user_id}:ticket")
        return None
    return await get_ticket_status(redis, ticket_id)