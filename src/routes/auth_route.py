from fastapi import APIRouter, Depends, Response

from src.controller.auth_controller import (
    LoginRequest,
    SignUpRequest,
    get_logged_in_user,
    login,
    logout,
    sign_up,
)
from src.middleware.auth_middleware import get_current_user


auth_router = APIRouter()

@auth_router.get("/me")
def logged_in_user_route(current_user=Depends(get_current_user)):
    return get_logged_in_user(current_user)

@auth_router.post("/sign_up")
def sign_up_route(payload: SignUpRequest, response: Response):
    return sign_up(payload, response)


@auth_router.post("/login")
def login_route(payload: LoginRequest, response: Response):
    return login(payload, response)


@auth_router.post("/logout")
def logout_route(response: Response):
    return logout(response)

