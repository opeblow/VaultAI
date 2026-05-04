from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware

from backend.routers import auth_router, payments_router, upload_router
from backend.database import Base, engine
from backend.models import *

app = FastAPI(
    title="Podcast AI SaaS API",
    description="API for Podcast AI processing, auth, payments",
    version="1.0.0",
    swagger_ui_parameters={"persistAuthorization": True},
)

# Configure BearerAuth security scheme
app.openapi_components = {
    "securitySchemes": {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
}

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add SlowAPI middleware for rate limiting
app.add_middleware(SlowAPIMiddleware)

# Include routers with prefixes
app.include_router(auth_router, prefix="/auth")
app.include_router(payments_router, prefix="/payments")
app.include_router(upload_router, prefix="/upload")

@app.on_event("startup")
def startup_event():
    """Create database tables on startup"""
    Base.metadata.create_all(bind=engine)
