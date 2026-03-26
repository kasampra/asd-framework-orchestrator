# src/app.py
from fastapi import FastAPI
from src.middleware import add_security_headers

app = FastAPI(title="Secure Hello World API", version="1.0")

# Explicitly apply security headers middleware BEFORE defining routes
add_security_headers(app)

@app.get("/hello")
def read_hello():
    return {"message": "Hello, World!"}