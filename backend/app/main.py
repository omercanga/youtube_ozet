from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import init_db
from .routers import api
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    init_db()
    yield


app = FastAPI(
    title="YouTube Transcript Analyzer",
    description="YouTube video & playlist transcript analysis API",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend origins
allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api.router)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/")
async def root():
    return {
        "message": "YouTube Transcript Analyzer API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
