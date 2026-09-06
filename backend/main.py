from dotenv import load_dotenv
import os

# 1. LOAD DOTENV FIRST
load_dotenv() 

from fastapi import FastAPI
from backend.api.routes import router as api_router
from backend.db import models, database
from fastapi.middleware.cors import CORSMiddleware

# Create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Job Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, change to your frontend URL
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def health_check():
    return {"status": "healthy"}