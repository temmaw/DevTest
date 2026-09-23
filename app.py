import os
import re
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Column, DateTime, Integer, String, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

# ============================================
# База данных
# ============================================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./data/weather.db"
)

connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_async_engine(DATABASE_URL, echo=False, connect_args=connect_args)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class WeatherRequest(Base):
    __tablename__ = "weather_requests"
    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, nullable=False)
    temperature = Column(String)
    humidity = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# ============================================
# Lifespan (вместо @app.on_event)
# ============================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    if "sqlite" in DATABASE_URL:
        os.makedirs("./data", exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print(f"✅ Database initialized: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
    yield
    await engine.dispose()


app = FastAPI(title="Weather Service", lifespan=lifespan)

# Фронт
app.mount("/static", StaticFiles(directory="static"), name="static")


# ============================================
# Эндпоинты
# ============================================
@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/weather")
async def get_weather(city: str = Query(..., description="City name"), db: AsyncSession = Depends(get_db)):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"https://wttr.in/{city}?format=%t+%h")
            response.raise_for_status()
            data = response.text.strip()
            print(f"Raw data from wttr.in: '{data}'")
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"API error: {str(e)}") from e

    temp = "N/A"
    humidity = "N/A"

    parts = [p.strip() for p in data.split('+') if p.strip()]
    print(f"Parts: {parts}")

    if len(parts) >= 2:
        for p in parts:
            if '°' in p or 'C' in p or 'F' in p:
                temp = p.strip()
                break
        for p in parts:
            if '%' in p:
                humidity = p.strip()
                break
    else:
        temp_match = re.search(r'([+-]?\d+°[CF])', data)
        if temp_match:
            temp = temp_match.group(1)
        humid_match = re.search(r'(\d+%)', data)
        if humid_match:
            humidity = humid_match.group(1)

    print(f"Parsed: temp={temp}, humidity={humidity}")

    record = WeatherRequest(city=city, temperature=temp, humidity=humidity)
    db.add(record)
    await db.commit()

    return {
        "city": city,
        "temperature": temp,
        "humidity": humidity,
        "saved": True
    }


@app.get("/history")
async def history(limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(WeatherRequest).order_by(WeatherRequest.created_at.desc()).limit(limit)
    )
    records = result.scalars().all()
    return [
        {
            "id": r.id,
            "city": r.city,
            "temperature": r.temperature,
            "humidity": r.humidity,
            "created_at": r.created_at,
        }
        for r in records
    ]
