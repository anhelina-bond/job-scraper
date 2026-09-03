from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from .database import Base

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

class AgentLog(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id"))
    step_name = Column(String)  # e.g., "scrape_job", "match_against_cv"
    tool_called = Column(String, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())