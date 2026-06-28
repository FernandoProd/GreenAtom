import redis.asyncio as aioredis
from config import REDIS_HOST, REDIS_PORT, REDIS_DB

# Не создаём клиент глобально, потому что lifespan будет управлять временем жизни.
# Но для удобства объявим переменную, которую проинициализируем позже.
redis_client: aioredis.Redis | None = None

async def init_redis():
    global redis_client
    redis_client = aioredis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True
    )

async def close_redis():
    if redis_client:
        await redis_client.close()