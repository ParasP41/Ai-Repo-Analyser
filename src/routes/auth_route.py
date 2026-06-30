from fastapi import APIRouter, Response

from src.controller.auth_controller import LoginRequest, SignUpRequest, login, logout, sign_up

auth_router = APIRouter()

@auth_router.post("/sign_up")
def sign_up_route(payload: SignUpRequest, response: Response):
    return sign_up(payload, response)


@auth_router.post("/login")
def login_route(payload: LoginRequest, response: Response):
    return login(payload, response)


@auth_router.post("/logout")
def logout_route(response: Response):
    return logout(response)
