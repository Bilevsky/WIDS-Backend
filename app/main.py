from fastapi import FastAPI

from app.routers import sensors, telemetry, whitelist

app = FastAPI(title="WIDS Backend")

app.include_router(sensors.router)
app.include_router(whitelist.router)
app.include_router(telemetry.router)

@app.get("/health")
async def health():
    return {"status": "ok"}