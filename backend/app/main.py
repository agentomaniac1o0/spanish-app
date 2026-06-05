from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import async_session, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    from app.crud import seed_database

    async with async_session() as db:
        await seed_database(db)
    yield


app = FastAPI(title="Spanish Learning Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def api_key_middleware(request, call_next):
    if request.url.path in ("/api/health", "/docs", "/openapi.json"):
        return await call_next(request)
    if settings.api_key:
        key = request.headers.get("X-API-Key", "")
        if key != settings.api_key:
            from fastapi.responses import JSONResponse

            return JSONResponse({"detail": "Invalid API key"}, status_code=401)
    return await call_next(request)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


from app.routers import conversation, lessons, placement, users, vocab

app.include_router(users.router, prefix="/api")
app.include_router(placement.router, prefix="/api")
app.include_router(lessons.router, prefix="/api")
app.include_router(vocab.router, prefix="/api")
app.include_router(conversation.router, prefix="/api")

app.mount("/static", StaticFiles(directory="static"), name="static")
