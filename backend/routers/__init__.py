from backend.routers.auth import router as auth_router
from backend.routers.payments import router as payments_router
from backend.routers.upload import router as upload_router

__all__ = ["auth_router", "payments_router", "upload_router"]
