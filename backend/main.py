from fastapi import FastAPI
from dotenv import load_dotenv
from app.routes import auth

load_dotenv()

app = FastAPI()

app.include_router(auth.router)

@app.get("/")
def read_root():
    return {"message": "Backend is running"}