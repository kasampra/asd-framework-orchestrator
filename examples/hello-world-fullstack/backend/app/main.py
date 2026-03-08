# backend/app/main.py
from fastapi import FastAPI

from app.endpoints.health import router as health_router
from app.endpoints.hello import router as hello_router

app = FastAPI(
    title="Hello World API",
    description="Minimal JWT-protected API for MVP",
    version="0.1.0",
)

app.include_router(health_router, prefix="/api")
app.include_router(hello_router, prefix="/api")