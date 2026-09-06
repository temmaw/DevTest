import sqlite3
import os
import re
from datetime import datetime
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx

app = FastAPI(title="Weather Service")

# Фронт
app.mount("/static", StaticFiles(directory="static"), name="static")

DB_PATH = os.getenv("DB_PATH", "/data/weather.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weather_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                temperature TEXT,
                humidity TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

@app.on_event("startup")
def startup():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    init_db()

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/weather")
async def get_weather(city: str = Query(..., description="City name")):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Формат с разделителями
            response = await client.get(
                f"https://wttr.in/{city}?format=%t+%h"
            )
            response.raise_for_status()
            data = response.text.strip()
            print(f"Raw data from wttr.in: '{data}'")  # Отладка
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"API error: {str(e)}")
    
    # Улучшенный парсинг
    temp = "N/A"
    humidity = "N/A"
    
    # Пробуем разные способы парсинга
    
    # Способ 1: через split по '+'
    parts = [p.strip() for p in data.split('+') if p.strip()]
    print(f"Parts: {parts}")  # Для отладки
    
    if len(parts) >= 2:
        # Ищем температуру (содержит °C или °F)
        for p in parts:
            if '°' in p or 'C' in p or 'F' in p:
                temp = p.strip()
                break
        # Ищем влажность (содержит %)
        for p in parts:
            if '%' in p:
                humidity = p.strip()
                break
    else:
        # Способ 2: через регулярные выражения
        # Ищем температуру: цифры + °C или °F
        temp_match = re.search(r'([+-]?\d+°[CF])', data)
        if temp_match:
            temp = temp_match.group(1)
        
        # Ищем влажность: цифры + %
        humid_match = re.search(r'(\d+%)', data)
        if humid_match:
            humidity = humid_match.group(1)
    
    print(f"Parsed: temp={temp}, humidity={humidity}")  # Для отладки
    
    with get_db() as conn:
        conn.execute(
            "INSERT INTO weather_requests (city, temperature, humidity) VALUES (?, ?, ?)",
            (city, temp, humidity)
        )
        conn.commit()
    
    return {
        "city": city,
        "temperature": temp,
        "humidity": humidity,
        "saved": True
    }

@app.get("/history")
async def history(limit: int = 10):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT city, temperature, humidity, created_at FROM weather_requests ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [dict(row) for row in rows]
