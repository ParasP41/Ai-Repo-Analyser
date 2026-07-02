import src.database.index
from fastapi import FastAPI
from src.routes.auth_route import auth_router
from src.routes.chat_route import chat_router
from src.routes.github_route import github_router


app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Welcome to the Repo Analyser API!"}


app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(github_router, prefix="/github", tags=["GitHub"])
app.include_router(chat_router, prefix="/chat", tags=["Chat"])
