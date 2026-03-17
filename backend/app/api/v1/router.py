from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, ese_eue

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(ese_eue.router)
