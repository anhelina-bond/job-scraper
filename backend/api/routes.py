from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from backend.db import models, database
from backend.agents.graph import app_agent  
from backend.db.database import get_db
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form  
from fastapi.responses import FileResponse
import shutil
import os
from backend.rag.cv_processor import index_cv
from backend.rag.retriever import delete_cv_from_index



router = APIRouter()

# Input Schema
class AnalyseRequest(BaseModel):
    url: Optional[str] = None
    manual_text: Optional[str] = None
    cv_id: int 

class FeedbackRequest(BaseModel):
    application_id: int
    feedback: str

router = APIRouter()

@router.get("/applications/{app_id}")
def get_application(app_id: int, db: Session = Depends(database.get_db)):
    # Join with CV table to get the label
    result = db.query(
        models.Application, 
        models.CV.label.label("cv_label")
    ).outerjoin(
        models.CV, models.Application.cv_id == models.CV.id
    ).filter(models.Application.id == app_id).first()

    if not result:
        raise HTTPException(status_code=404, detail="Application not found")
    
    app, cv_label = result
    # Convert SQLAlchemy object to dict and add the label
    data = {c.name: getattr(app, c.name) for c in app.__table__.columns}
    data["cv_label"] = cv_label
    return data

@router.get("/cvs")
def get_cvs(db: Session = Depends(get_db)):
    return db.query(models.CV).order_by(models.CV.created_at.desc()).all()




@router.post("/cvs/upload")
async def upload_cv(
    label: str = Form(...),             # <--- Add = Form(...) here
    file: UploadFile = File(...), 
    db: Session = Depends(database.get_db)
):
    # Ensure the uploads directory exists
    os.makedirs("uploads", exist_ok=True)
    
    file_location = f"uploads/{file.filename}"
    
    # Save the file to disk
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Save metadata to Database
    new_cv = models.CV(
        filename=file.filename,
        label=label,
        file_path=file_location
    )
    db.add(new_cv)
    db.commit()
    db.refresh(new_cv)
    
    # Index in ChromaDB (Pass the ID so we can filter later)
    try:
        index_cv(file_location, cv_id=new_cv.id)
    except Exception as e:
        print(f"Indexing error: {e}")
        # We don't want to crash the whole request if indexing fails, 
        # but in production, you'd handle this better.
    
    return {"id": new_cv.id, "label": label, "filename": file.filename}

@router.delete("/cvs/{cv_id}")
def delete_cv(cv_id: int, db: Session = Depends(database.get_db)):
    # 1. Find the CV in the database
    db_cv = db.query(models.CV).filter(models.CV.id == cv_id).first()
    
    if not db_cv:
        raise HTTPException(status_code=404, detail="CV not found")

    try:
        # 2. Delete the physical file from the 'uploads' folder
        if os.path.exists(db_cv.file_path):
            os.remove(db_cv.file_path)

        # 3. Delete from ChromaDB
        delete_cv_from_index(cv_id)

        # 4. Delete the record from PostgreSQL
        db.delete(db_cv)
        db.commit()

        return {"message": f"Successfully deleted CV {cv_id} and associated data."}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error during deletion: {str(e)}")

@router.get("/api/cvs") # Add this if missing
def list_cvs(db: Session = Depends(database.get_db)):
    return db.query(models.CV).all()

@router.post("/re-evaluate")
async def re_evaluate(request: FeedbackRequest, db: Session = Depends(get_db)):
    app_record = db.query(models.Application).filter(models.Application.id == request.application_id).first()
    
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")

    # RECONSTRUCT FULL STATE FROM DB
    current_state = {
        "job_url": app_record.job_url,           # Helpful for context
        "job_title": app_record.job_title,
        "company_name": app_record.company,     # Ensure this matches your AgentState key
        "requirements": app_record.requirements, 
        "cv_matches": app_record.cv_matches,    
        "cover_letter": app_record.cover_letter,
        "human_feedback": request.feedback,     # This triggers the "Revision" logic
        "raw_text": app_record.raw_job_text,
        "cv_id": app_record.cv_id,   
    }
    
    try:
        # Run the agent (it will start from the generation node)
        revised_state = app_agent.invoke(current_state) 
        
        # Update the DB with the new letter and the NEW evaluation
        app_record.cover_letter = revised_state["cover_letter"]
        app_record.evaluation = revised_state["evaluation"]
        
        db.commit()
        
        return {
            "id": app_record.id,
            "cover_letter": app_record.cover_letter,
            "evaluation": app_record.evaluation,
            "match_score": app_record.match_score,
            "requirements_analysis": app_record.cv_matches
        }
    except Exception as e:
        print(f"Re-evaluation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyse")
async def analyse_job(request: AnalyseRequest, db: Session = Depends(get_db)):
    if not request.url and not request.manual_text:
        raise HTTPException(status_code=400, detail="Provide either a URL or job text.")

    # 1. Initialize Agent State
    initial_state = {
        "job_url": request.url,
        "raw_text": request.manual_text if request.manual_text else None,
        "status": "starting",
        "cv_id": request.cv_id,  
        "requirements": [],
        "cv_matches": []
    }

    try:
        # 2. Run the LangGraph Agent
        # .invoke() runs the graph until END
        final_state = app_agent.invoke(initial_state)

        new_app = models.Application(
            job_url=final_state.get("job_url"),
            job_title=final_state.get("job_title"),
            company=final_state.get("company_name"),
            match_score=final_state.get("match_score"),
            cover_letter=final_state.get("cover_letter"),
            raw_job_text=final_state.get("raw_text"),
            requirements=final_state.get("requirements"),
            cv_matches=final_state.get("cv_matches"),
            evaluation=final_state.get("evaluation"),
            cv_id=request.cv_id, 
        )
        db.add(new_app)
        db.flush()  # Flushes to get the new_app.id before committing

        # 4. Save to PostgreSQL: Logs Table
        # In a real agent, you might log every single step. 
        # Here we save a summary log entry for the whole run.
        execution_log = models.AgentLog(
            application_id=new_app.id,
            step_name="full_run",
            input_data={"url": request.url},
            output_data={
                "requirements": final_state.get("requirements"),
                "match_score": final_state.get("match_score")
            }
        )
        db.add(execution_log)
        
        db.commit()
        db.refresh(new_app)

        # 5. Return everything the frontend needs
        return {
            "id": new_app.id,
            "job_title": new_app.job_title,
            "company": new_app.company,
            "match_score": new_app.match_score,
            "requirements_analysis": final_state.get("cv_matches"),
            "cover_letter": new_app.cover_letter
        }

    except Exception as e:
        db.rollback()
        print(f"Agent Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/applications")
def get_applications(db: Session = Depends(database.get_db)):
    # Join Application with CV to get the label for each history item
    results = db.query(
        models.Application, 
        models.CV.label.label("cv_label")
    ).outerjoin(
        models.CV, models.Application.cv_id == models.CV.id
    ).order_by(models.Application.date_applied.desc()).all()

    output = []
    for app, cv_label in results:
        # Convert SQLAlchemy model to a dict
        app_dict = {c.name: getattr(app, c.name) for c in app.__table__.columns}
        app_dict["cv_label"] = cv_label
        output.append(app_dict)

    return output



@router.get("/cvs/{cv_id}/view")
def view_cv(cv_id: int, db: Session = Depends(database.get_db)):
    db_cv = db.query(models.CV).filter(models.CV.id == cv_id).first()
    if not db_cv or not os.path.exists(db_cv.file_path):
        raise HTTPException(status_code=404, detail="CV File not found")
    
    # This returns the file directly to the browser
    return FileResponse(db_cv.file_path, media_type='application/pdf')