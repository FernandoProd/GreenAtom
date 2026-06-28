from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request
import httpx
import redis.asyncio as aioredis
from config import REDIS_HOST, REDIS_PORT, REDIS_DB
from schemas import CreateTicketRequest, TicketResponse, DeleteResponse
from services import check_user_exists, create_ticket, delete_ticket, get_ticket_status, get_ticket_by_user
from fastapi.middleware.cors import CORSMiddleware

# ------------------ Lifespan ------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск: создаём пул соединений HTTP и Redis
    async with httpx.AsyncClient() as http_client:
        redis = aioredis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )
        # Сохраняем в app.state, чтобы доставать в зависимостях
        app.state.http_client = http_client
        app.state.redis = redis
        yield
        # Завершение: закрываем Redis (httpx закроется сам через async with)
        await redis.close()

app = FastAPI(title="TicketService", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для разработки разрешим все, в проде сузить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ Зависимости ------------------
def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client

def get_redis(request: Request) -> aioredis.Redis:
    return request.app.state.redis

# ------------------ Эндпоинты ------------------
@app.post("/tickets", response_model=TicketResponse, status_code=201)
async def create_ticket_endpoint(
    data: CreateTicketRequest,
    http_client: httpx.AsyncClient = Depends(get_http_client),
    redis: aioredis.Redis = Depends(get_redis)
):
    exists = await check_user_exists(http_client, data.user_id)
    if not exists:
        raise HTTPException(status_code=404, detail="User not found")
    ticket = await create_ticket(redis, data.user_id)
    return ticket


@app.get("/tickets/by-user/{user_id}", response_model=TicketResponse)
async def get_ticket_by_user_endpoint(
    user_id: str,
    redis: aioredis.Redis = Depends(get_redis)
):
    ticket = await get_ticket_by_user(redis, user_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="No active ticket for this user")
    return ticket


@app.delete("/tickets/{ticket_id}", response_model=DeleteResponse)
async def delete_ticket_endpoint(
    ticket_id: str,
    redis: aioredis.Redis = Depends(get_redis)
):
    deleted = await delete_ticket(redis, ticket_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"message": f"Ticket {ticket_id} deleted"}

@app.get("/tickets/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    redis: aioredis.Redis = Depends(get_redis)
):
    status = await get_ticket_status(redis, ticket_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"ticket_id": ticket_id, "status": status}

@app.get("/health")
async def health(redis: aioredis.Redis = Depends(get_redis)):
    try:
        await redis.ping()
        return {"status": "ok", "redis": "connected"}
    except Exception:
        return {"status": "error", "redis": "disconnected"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)