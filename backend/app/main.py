from fastapi import FastAPI
from sqlalchemy import text
from app.db import engine
from app.routers import users

app = FastAPI(title="K-LOG API")

app.include_router(users.router)

@app.get("/health/db")
def health_db():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}
