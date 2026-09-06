from langgraph.graph import StateGraph, END
from .state import AgentState
from ..tools.scraper import scrape_job_posting
from ..rag.retriever import query_cv  # Assuming you built this in Phase 2
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# --- NODE 1: Scrape Job ---
def scrape_job_node(state: AgentState):
    print("---SKILL: SCRAPING JOB---")
    if state.get("raw_text"): # User pasted text manually
        return {"status": "analyzing", "raw_text": state["raw_text"]}
    
    result = scrape_job_posting(state["job_url"])
    if result["success"]:
        return {"raw_text": result["raw_text"], "status": "analyzing"}
    else:
        raise ValueError("Scraping failed and no raw text provided.")

# --- NODE 2: Analyse Requirements ---
def analyze_requirements_node(state: AgentState):
    print(f"--- SKILL: ANALYZING REQUIREMENTS (Text length: {len(state['raw_text'] or '')}) ---")
    
    if not state["raw_text"] or len(state["raw_text"]) < 50:
        # If scraper failed, we shouldn't even try the LLM
        return {
            "job_title": "Unknown",
            "company_name": "Unknown",
            "requirements": ["Scraper failed to get job text"],
            "nice_to_haves": [],
            "status": "matching"
        }

    prompt = f"""
    Extract the following from this job description:
    1. Job Title
    2. Company Name
    3. Top 5 Technical Requirements (as a list of strings)
    4. Nice-to-have skills (as a list of strings)
    
    Return ONLY a valid JSON object.
    
    Job Text: {state['raw_text'][:4000]}
    """
    
    response = llm.invoke(prompt)
    # Use the helper to handle "Chatter"
    data = extract_json(response.content)
    
    return {
        "job_title": data.get('job_title', 'Unknown'),
        "company_name": data.get('company', 'Unknown'),
        "requirements": data.get('requirements', []),
        "nice_to_haves": data.get('nice_to_haves', []),
        "status": "matching"
    }

# --- NODE 3: Match against CV ---
def match_against_cv_node(state: AgentState):
    print("--- SKILL: MATCHING AGAINST CV ---")
    matches = []
    
    for req in state["requirements"]:
        relevant_chunks = query_cv(req)
        
        score_prompt = f"""
        Requirement: {req}
        CV Evidence: {relevant_chunks}
        Return a JSON object: {{"score": 0-100, "reasoning": "string"}}
        """
        
        response = llm.invoke(score_prompt)
        try:
            match_data = extract_json(response.content)
            matches.append({
                "requirement": req,
                "score": match_data.get("score", 0),
                "reasoning": match_data.get("reasoning", "N/A")
            })
        except:
            matches.append({"requirement": req, "score": 0, "reasoning": "Failed to parse score"})

    avg_score = sum(m["score"] for m in matches) / len(matches) if matches else 0
    return {"cv_matches": matches, "match_score": avg_score, "status": "generating"}

# --- NODE 4: Generate Output ---
def generate_output_node(state: AgentState):
    print("---SKILL: GENERATING COVER LETTER---")
    prompt = f"""
    Write a tailored, professional cover letter for the {state['job_title']} role at {state['company_name']}.
    Use these specific CV matches to prove experience: {state['cv_matches']}
    
    Tone: Professional, enthusiastic, and evidence-based.
    """
    cover_letter = llm.invoke(prompt).content
    return {"cover_letter": cover_letter, "status": "completed"}

import json
import re

def extract_json(text: str) -> dict:
    """Helper to extract JSON from LLM response even if it contains chatter."""
    try:
        # Look for content between curly braces
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(text)
    except Exception:
        print(f"FAILED TO PARSE JSON. Raw text: {text}")
        raise

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("scrape_job", scrape_job_node)
workflow.add_node("analyze_requirements", analyze_requirements_node)
workflow.add_node("match_cv", match_against_cv_node)
workflow.add_node("generate_output", generate_output_node)

# Set Edges (The Flow)
workflow.set_entry_point("scrape_job")
workflow.add_edge("scrape_job", "analyze_requirements")
workflow.add_edge("analyze_requirements", "match_cv")
workflow.add_edge("match_cv", "generate_output")
workflow.add_edge("generate_output", END)

# Compile
app_agent = workflow.compile()