"""User routes package"""

from fastapi import APIRouter

from app.users.routes.auth import router as auth_router
from app.users.routes.users import router as users_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(users_router, prefix="/users", tags=["Users"])
