import src.database.index
from src.routes.auth_route import auth_router
from src.routes.github_route import github_router
from fastapi import FastAPI


app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Repo Analyser API!"}



app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(github_router, prefix="/github", tags=["GitHub"])