import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import analyze, health

app = FastAPI(
    title="多 Agent 台股智慧分析 API",
    description="Next.js 新版儀表板使用的 FastAPI mock backend。",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(analyze.router, prefix="/api", tags=["analyze"])

if os.getenv("ENABLE_DEBUG_ENDPOINTS") == "true":
    from app.routers import debug

    app.include_router(debug.router, prefix="/api", tags=["debug"])
