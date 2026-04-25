"""
VaultAI Backend Application

This is the main entry point for the VaultAI FastAPI backend application.
It initializes the database, ML pipeline, and registers all API routers.

Production-grade implementation with:
- FastAPI latest version
- SQLite database with SQLAlchemy ORM
- JWT authentication
- CORS enabled for all origins
- Background tasks for ML processing
- Swagger UI and ReDoc documentation
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.database import create_tables
from backend.models.schemas import HealthCheckResponse
from backend.routers import (
    auth_router,
    ingest_router,
    query_router,
    vaults_router,
    payments_router
)
from backend.routers.ingest import set_pipeline as set_ingest_pipeline


ml_pipeline = None


def initialize_ml_pipeline():
    global ml_pipeline
    
    try:
        from ml.pipelines.podcast_pipeline import PodcastPipeline
        
        pipeline = PodcastPipeline()
        
        set_ingest_pipeline(pipeline)
        
        ml_pipeline = pipeline
        return pipeline
        
    except ImportError:
        print("Warning: ML pipeline not available. Install ml-pipeline package.")
        return None
    except Exception as e:
        print(f"Warning: Failed to initialize ML pipeline: {str(e)}")
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    
    initialize_ml_pipeline()
    
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)
    os.makedirs(os.path.join(settings.STORAGE_PATH, "users"), exist_ok=True)
    
    yield
    
    global ml_pipeline
    ml_pipeline = None


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## VaultAI - AI Audio Intelligence Platform

VaultAI is a production-grade AI audio intelligence platform that helps users:

- **Upload and process podcast audio files**
- **Get AI-generated summaries and insights**
- **Query podcasts with natural language**
- **Manage subscription plans**

### Authentication

Most endpoints require JWT authentication. To authenticate:
1. Register a new user at `/auth/register`
2. Login at `/auth/login` to get an access token
3. Include the token in the Authorization header: `Bearer <token>`

### Plans

- **Free**: 3 episodes maximum
- **Creator**: 20 episodes maximum
- **Studio**: Unlimited episodes
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ingest_router)
app.include_router(query_router)
app.include_router(vaults_router)
app.include_router(payments_router)


@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Health Check"],
    summary="Health check endpoint",
    description="Returns the health status of the VaultAI API."
)
def health_check():
    return HealthCheckResponse(
        status="healthy",
        message="VaultAI API is running"
    )


@app.get(
    "/",
    tags=["Root"],
    summary="Root endpoint",
    description="Returns welcome message and API information."
)
def root():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health"
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )

    