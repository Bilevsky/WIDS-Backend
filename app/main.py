from fastapi import FastAPI

app = FastAPI(title="WIDS Backend")


@app.get("/health")
async def health():
    return {"status": "ok"}