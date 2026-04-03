from fastapi import APIRouter
from app.api.endpoints import users, records, feed, auth

api_router = APIRouter()

api_router.include_router(users.router, prefix="/user", tags=["user"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(records.router, prefix="/record", tags=["record"])
api_router.include_router(feed.router, prefix="/feed", tags=["feed"])

