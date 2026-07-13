from fastapi import APIRouter

from boutique.presentation.http.routers.auth import router as auth_router
from boutique.presentation.http.routers.dashboard import router as dashboard_router
from boutique.presentation.http.routers.dataset import router as dataset_router
from boutique.presentation.http.routers.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(dashboard_router)
api_router.include_router(dataset_router)
