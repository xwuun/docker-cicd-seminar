import os

import psycopg
from fastapi import FastAPI, HTTPException

app = FastAPI()


@app.get("/")
def health():
    return {"message": "hello docker"}


@app.get("/db")
def database_health():
    url = os.getenv("DATABASE_URL")
    if not url:
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured")

    try:
        with psycopg.connect(url, connect_timeout=3) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                value = cursor.fetchone()[0]
    except psycopg.Error:
        raise HTTPException(status_code=503, detail="Database is unavailable") from None

    return {"database": "ok", "value": value}