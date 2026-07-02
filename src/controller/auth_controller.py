from fastapi import HTTPException, Response, status
from pydantic import BaseModel, EmailStr, Field

from src.models.auth_model import User, users
from src.utils.hashing import hash_password, verify_password
from src.utils.jwt import clear_auth_cookie, create_access_token, set_auth_cookie


class SignUpRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


def user_response(user: dict):
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
    }


def sign_up(payload: SignUpRequest, response: Response):
    existing_user = users.find_one({
        "$or": [
            {"email": payload.email},
            {"username": payload.username},
        ]
    })
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email or username already exists",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    user_data = user.model_dump(by_alias=True, exclude_none=True)
    result = users.insert_one(user_data)

    saved_user = {
        "_id": result.inserted_id,
        "username": payload.username,
        "email": payload.email,
    }
    token = create_access_token({"sub": str(result.inserted_id)})
    set_auth_cookie(response, token)

    return {
        "message": "User created successfully",
        "user": user_response(saved_user),
    }


def login(payload: LoginRequest, response: Response):
    user = users.find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": str(user["_id"])})
    set_auth_cookie(response, token)

    return {
        "message": "Login successful",
        "user": user_response(user),
    }


def logout(response: Response):
    clear_auth_cookie(response)
    return {"message": "Logout successful"}


def get_logged_in_user(current_user: dict):
    return {
        "user": user_response(current_user),
    }
