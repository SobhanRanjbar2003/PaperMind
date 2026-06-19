from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.services.llm_client import aclose_client

app = FastAPI(title="Book Summarizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("shutdown")
async def shutdown_event():
    await aclose_client()


@app.get("/")
async def root():
    return {"status": "ok", "service": "book-summarizer-api"}
