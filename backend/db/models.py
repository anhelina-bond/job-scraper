from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from .database import Base

class CV(Base):
    __tablename__ = "cvs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    label = Column(String)
    file_path = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    job_url = Column(String, nullable=True)
    job_title = Column(String)
    company = Column(String)
    date_applied = Column(DateTime(timezone=True), server_default=func.now())
    match_score = Column(Float)
    cover_letter = Column(Text)
    raw_job_text = Column(Text)
    requirements = Column(JSON, nullable=True)   # Stores the list of extracted reqs
    cv_matches = Column(JSON, nullable=True)     # Stores the list of match evidence
    evaluation = Column(JSON, nullable=True)     # Stores the latest AI critic result
    cv_id = Column(Integer, ForeignKey("cvs.id"), nullable=True)

class AgentLog(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    step_name = Column(String)  # e.g., "scrape_job", "match_against_cv"
    tool_called = Column(String, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())