from fastapi import FastAPI
from dotenv import load_dotenv
from app.routes import auth, files, folders, shares

load_dotenv()

app = FastAPI()

app.include_router(auth.router)
app.include_router(files.router)
app.include_router(folders.router)
app.include_router(shares.router)

@app.get("/")
def read_root():
    return {"message": "Backend is running"}