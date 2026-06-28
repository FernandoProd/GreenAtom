from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request
import redis.asyncio as aioredis
from config import REDIS_HOST, REDIS_PORT, REDIS_DB
from schemas import (
    UserRegisterRequest, UserLoginRequest,
    RegisterResponse, LoginResponse, UserResponse
)
from services import register_user, authenticate_user, get_user
from fastapi.middleware.cors import CORSMiddleware

# ------------------ Lifespan ------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаём асинхронный Redis-клиент
    redis = aioredis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True
    )
    app.state.redis = redis
    yield
    # Закрываем подключение при завершении
    await redis.close()

app = FastAPI(title="UserService", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для разработки разрешим все, в проде сузить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ Зависимости ------------------
def get_redis(request: Request) -> aioredis.Redis:
    return request.app.state.redis

# ------------------ Эндпоинты ------------------
@app.post("/register", response_model=RegisterResponse, status_code=201)
async def register(data: UserRegisterRequest, redis: aioredis.Redis = Depends(get_redis)):
    try:
        user_id = await register_user(redis, data.email, data.password)
        return {"user_id": user_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login", response_model=LoginResponse)
async def login(data: UserLoginRequest, redis: aioredis.Redis = Depends(get_redis)):
    try:
        user_id = await authenticate_user(redis, data.email, data.password)
        return {"user_id": user_id, "message": "Authenticated"}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user_endpoint(user_id: str, redis: aioredis.Redis = Depends(get_redis)):
    user = await get_user(redis, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/health")
async def health(redis: aioredis.Redis = Depends(get_redis)):
    try:
        await redis.ping()
        return {"status": "ok", "redis": "connected"}
    except Exception:
        return {"status": "error", "redis": "disconnected"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

# http://127.0.0.1:8000/docs