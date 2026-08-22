from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Backend is running"}

@app.get("/test-env")
def test_env():
    return {"supabase_url_loaded": os.getenv("SUPABASE_URL") is not None}