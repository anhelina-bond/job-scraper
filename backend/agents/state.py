from typing import TypedDict, List, Optional, Dict, Any

class AgentState(TypedDict):
    # Input
    job_url: Optional[str]
    raw_text: Optional[str]  # Used if URL scraping fails or user pastes text
    
    # Processed Data
    job_title: Optional[str]
    company_name: Optional[str]
    requirements: List[str]
    nice_to_haves: List[str]
    
    # RAG Results
    cv_matches: List[Dict[str, Any]] # Matches for each requirement
    match_score: float
    
    # Final Output
    cover_letter: Optional[str]
    report: Optional[str]
    
    # Metadata for DB Logging
    status: str