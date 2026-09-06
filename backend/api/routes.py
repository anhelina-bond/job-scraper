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

@router.post("/analyse")
async def analyse_job(request: AnalyseRequest, db: Session = Depends(get_db)):
    if not request.url and not request.manual_text:
        raise HTTPException(status_code=400, detail="Provide either a URL or job text.")

    # 1. Initialize Agent State
    initial_state = {
        "job_url": request.url,
        "raw_text": request.manual_text,
        "status": "starting",
        "requirements": [],
        "cv_matches": []
    }

    try:
        # 2. Run the LangGraph Agent
        # .invoke() runs the graph until END
        final_state = app_agent.invoke(initial_state)

        # 3. Save to PostgreSQL: Applications Table
        new_app = models.Application(
            job_url=final_state.get("job_url"),
            job_title=final_state.get("job_title"),
            company=final_state.get("company_name"),
            match_score=final_state.get("match_score"),
            cover_letter=final_state.get("cover_letter"),
            raw_job_text=final_state.get("raw_text")
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