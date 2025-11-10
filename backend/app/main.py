from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.middleware import RateLimitMiddleware
from app.api import routes
from app.services.cache import cache_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to Redis
    await cache_service.connect()
    yield
    # Shutdown: Disconnect from Redis
    await cache_service.disconnect()

app = FastAPI(
    title="TerpTracker API",
    description="Cannabis strain terpene profile analyzer",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)

# Include API routes
app.include_router(routes.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "TerpTracker API", "version": "0.1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
