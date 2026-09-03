from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .db import models, schemas, database

# Create tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Job Agent API")

# Root endpoint
@app.get("/")
def read_root():
    return {"status": "Agent API is online"}

# TEST ENDPOINT: Create a dummy application to verify DB
@app.post("/test-db", response_model=schemas.ApplicationResponse)
def test_db(db: Session = Depends(database.get_db)):
    new_app = models.Application(
        job_title="Software Engineer",
        company="Tech Corp",
        match_score=85.0,
        cover_letter="Hello, I am a dev...",
        job_url="http://example.com"
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)
    return new_app