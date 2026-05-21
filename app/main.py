import logging

from fastapi import FastAPI
from app.routers.departments import router as department_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

app = FastAPI(title="Org Structure API", version="1.0.0")
app.include_router(department_router, prefix="/api/v1")

@app.get("/", include_in_schema=False)
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["health"])
async def health():
    return {"status", "ok"}