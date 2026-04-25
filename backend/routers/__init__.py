"""
VaultAI Routers Package

This package contains all API routers for the VaultAI application.
Routers are organized by functional area: auth, ingest, query, vaults, and payments.
"""

from fastapi import APIRouter

from backend.routers.auth import router as auth_router
from backend.routers.ingest import router as ingest_router
from backend.routers.query import router as query_router
from backend.routers.vaults import router as vaults_router
from backend.routers.payments import router as payments_router

__all__ = [
    "auth_router",
    "ingest_router", 
    "query_router",
    "vaults_router",
    "payments_router"
]