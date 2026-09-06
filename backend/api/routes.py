from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from backend.db import models, database
from backend.agents.graph import app_agent  # The compiled LangGraph
from backend.db.database import get_db

router = APIRouter()

# Input Schema
class AnalyseRequest(BaseModel):
    url: Optional[str] = None
    manual_text: Optional[str] = None

class FeedbackRequest(BaseModel):
    application_id: int
    feedback: str

@router.post("/re-evaluate")
async def re_evaluate(request: FeedbackRequest, db: Session = Depends(get_db)):
    app_record = db.query(models.Application).filter(models.Application.id == request.application_id).first()
    
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")

    # RECONSTRUCT FULL STATE FROM DB
    current_state = {
        "job_title": app_record.job_title,
        "company_name": app_record.company,
        "requirements": app_record.requirements, # Pulled from DB
        "cv_matches": app_record.cv_matches,     # Pulled from DB
        "cover_letter": app_record.cover_letter,
        "human_feedback": request.feedback,
        "raw_text": app_record.raw_job_text
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
        print(f"HITL Error: {e}")
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
            evaluation=final_state.get("evaluation")
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
def get_applications(db: Session = Depends(get_db)):
    return db.query(models.Application).order_by(models.Application.date_applied.desc()).all()