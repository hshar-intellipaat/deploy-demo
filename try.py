from fastapi import FastAPI
from supabase import create_client, Client
import os
from dotenv import load_dotenv
load_dotenv()
app = FastAPI()


@app.get("/")
def read_root():
    text = "Hello World from FastAPI!"
    return {text}