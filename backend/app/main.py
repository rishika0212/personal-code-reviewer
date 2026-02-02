from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.review_routes import router as review_router
from api.repo_routes import router as repo_router
from config import settings

app = FastAPI(
    title="Coder - AI Code Review",
    description="Multi-agent code review system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review_router, prefix="/api/review", tags=["review"])
app.include_router(repo_router, prefix="/api/repo", tags=["repo"])


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
