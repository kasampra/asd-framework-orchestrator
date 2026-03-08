# backend/app/config.py
import os
from dotenv import load_dotenv
from fastapi import HTTPException
import sys

load_dotenv()

class Settings:
    JWT_SECRET: str = os.getenv("JWT_SECRET", "")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_SECONDS: int = int(os.getenv("JWT_EXPIRY_SECONDS", "3600"))  # default 1 hour

settings = Settings()

# 🔐 SECURITY: Validate JWT secret is non-empty before app starts
if not settings.JWT_SECRET:
    raise HTTPException(
        status_code=500,
        detail="JWT_SECRET environment variable must be set to a non-empty value for production security."
    )