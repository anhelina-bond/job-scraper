from langgraph.graph import StateGraph, END
from .state import AgentState
from ..tools.scraper import scrape_job_posting
from ..rag.retriever import query_cv  # Assuming you built this in Phase 2
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import json
import re

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# --- NODE 1: Scrape Job ---
def scrape_job_node(state: AgentState):
    if state.get("raw_text") and len(state["raw_text"]) > 50:
        return {"status": "analyzing"}
    
    print("--- NODE: SCRAPE JOB ---")
    
    # 1. If user already provided manual text, SKIP scraping
    if state.get("raw_text") and len(state["raw_text"]) > 20:
        print("Using manual text provided by user.")
        return {"status": "analyzing"}

    # 2. Otherwise, attempt to scrape
    if not state.get("job_url"):
        return {"raw_text": "ERROR: No URL or text provided", "status": "failed"}

    result = scrape_job_posting(state["job_url"])
    
    if result["success"] and len(result["raw_text"]) > 100:
        return {"raw_text": result["raw_text"], "status": "analyzing"}
    else:
        # We return a specific string that the next node can recognize as a failure
        return {"raw_text": "BLOCK_SCRAPER_FAIL", "status": "failed"}

# --- NODE 2: Analyse Requirements ---
def analyze_requirements_node(state: AgentState):
    if state.get("requirements") and len(state["requirements"]) > 0:
        return {"status": "matching"}
    
    print("--- NODE: ANALYZE REQUIREMENTS ---")
    raw_text = state.get("raw_text", "")

    # GUARDRAIL: If text is missing or indicates a scraper failure, STOP.
    if "BLOCK_SCRAPER_FAIL" in raw_text or len(raw_text) < 50:
        print("Aborting: Job text is insufficient for analysis.")
        return {
            "job_title": "N/A",
            "company_name": "N/A",
            "requirements": [], # Empty list prevents matching
            "status": "failed"
        }

    prompt = f"""
    You are a professional recruiter. Extract the job requirements from this text.
    If the text is junk, empty, or does not contain a job description, return an empty JSON.
    
    Job Text: {raw_text[:4000]}
    
    Return JSON: {{"job_title": "...", "company": "...", "requirements": ["req1", "req2"]}}
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
    if state.get("human_feedback") and state.get("cv_matches"):
        print("--- SKIPPING MATCHING: Using existing matches for revision ---")
        return {"status": "generating"}

    print(f"--- SKILL: MATCHING AGAINST CV (ID: {state.get('cv_id')}) ---")
    matches = []
    
    for req in state["requirements"]:
        relevant_chunks = query_cv(req, cv_id=state["cv_id"]) 
        
        score_prompt = f"""
            You are a strict technical recruiter doing CV screening.

            Job Requirement: {req}
            CV Evidence Retrieved: {relevant_chunks}

            Score this match from 0 to 100 using these STRICT rules:

            - 0-10: The requirement is completely absent from the CV. No mention, no related technology, nothing.
            - 11-30: The CV mentions something vaguely related but it is a stretch. The candidate would struggle to demonstrate this in an interview.
            - 31-55: The CV shows indirect or foundational exposure — adjacent technology or a related concept, but not the exact requirement.
            - 56-75: The CV shows clear evidence of this skill from a real project or internship, but limited depth or only one example.
            - 76-90: The CV shows solid, repeated evidence across multiple projects or a professional context.
            - 91-100: The CV directly and strongly demonstrates this requirement with specific, verifiable examples.

            IMPORTANT RULES:
            - If the retrieved CV evidence does not contain any direct mention of the requirement, the score MUST be below 30.
            - Do NOT give benefit of the doubt. If it is not in the CV, it is not in the CV.
            - Do NOT assume transferable skills unless the CV explicitly demonstrates them being transferred.
            - Knowing Python does not mean knowing FastAPI. Using React does not mean knowing Vue.js.

            Return ONLY this JSON:
            {{
                "score": <integer 0-100>,
                "reasoning": "<one specific sentence explaining the score, citing actual CV evidence or lack of it>",
                "is_absent": <true if requirement is completely missing from CV, false otherwise>
            }}
"""
        
        response = llm.invoke(score_prompt)
        try:
            match_data = extract_json(response.content)
            matches.append({
                "requirement": req,
                "score": match_data.get("score", 0),
                "reasoning": match_data.get("reasoning", "N/A"),
                "is_absent": match_data.get("is_absent", False) 
            })
        except:
            matches.append({"requirement": req, "score": 0, "reasoning": "Failed to parse score"})

    avg_score = sum(m["score"] for m in matches) / len(matches) if matches else 0
    return {"cv_matches": matches, "match_score": avg_score, "status": "generating"}

# --- NODE 4: Generate Output ---
def evaluate_output_node(state: AgentState):
    print("--- NODE: CRITIC (Gap Analysis Mode) ---")
    
    letter = state.get("cover_letter")
    requirements = state.get("requirements")
    company = state.get("company_name")
    cv_matches = state.get("cv_matches")
    
    prompt = f"""
        You are a blunt Technical Hiring Manager at {company} who rejects 80% of applicants.

        Your job is to find weaknesses, not validate the candidate.

        Cover Letter to critique:
        {letter}

        Job Requirements:
        {requirements}

        CV Evidence actually available:
        {cv_matches}

        CRITICAL CHECKS — flag every one that applies:

        1. ABSENT SKILLS: Does the letter claim or imply skills that have a score below 30 in cv_matches? 
        This is a red flag — the candidate is overclaiming.
        
        2. UNSUBSTANTIATED CLAIMS: Does the letter make generic statements 
        ("strong problem-solver", "fast learner") without tying them to a specific project or result?
        
        3. MISSING CORE REQUIREMENTS: Which requirements from the list are not addressed at all?

        4. SPECIFICITY: Does the letter cite actual project names and real technical details, 
        or does it speak in vague generalities?

        5. COMPANY FIT: Does the opening paragraph say something specific about {company} 
        or could it be copy-pasted to any job application?

        SCORING:
        - 85-100: Every core requirement addressed with real evidence. Zero overclaiming. Company-specific opening.
        - 65-84: Solid, but 1 core requirement missing or 1 unsupported claim.
        - 45-64: Missing evidence for multiple requirements OR making claims the CV cannot back up.
        - Below 45: Generic template, overclaims absent skills, or ignores core requirements entirely.

        Be harsh. A score above 80 should be rare.

        Return ONLY this JSON:
        {{
            "score": <integer 0-100>,
            "critique": "<one blunt sentence identifying the single biggest weakness>",
            "missing_points": ["<specific requirement not addressed>"],
            "overclaimed_skills": ["<skill claimed in letter but absent or weak in CV>"],
            "is_robotic": <true/false>
        }}
        """
    
    response = llm.invoke(prompt)
    eval_data = extract_json(response.content)
    return {"evaluation": eval_data}

def generate_output_node(state: AgentState):
    print("--- NODE: GENERATE/REVISE (Anti-Robotic Mode) ---")
    
    # 1. Gather the "Context"
    feedback = state.get("human_feedback", "")
    matches = state.get("cv_matches", [])
    job_title = state.get("job_title")
    company = state.get("company_name")

    # 2. The Enhanced Prompt
    prompt = f"""
    You are an elite Career Coach and Senior Engineer. Write a cover letter for the {job_title} role at {company}.

    CV EVIDENCE TO USE (Be specific!):
    {matches}

    USER'S ADDITIONAL NOTES:
    {feedback}

    CRITICAL INSTRUCTIONS (To sound human and avoid 'AI' detection):
    1. SHOW, DON'T TELL: Instead of saying "I have strong TypeScript skills," say "I implemented a type-safe architecture using TypeScript that reduced production bugs by X%." (Use the metrics from the CV matches).
    2. THE "FORBIDDEN" LIST: Do NOT use these robotic words: "honed", "passionate about", "tapestry", "leverage", "comprehensive", "exciting opportunity", "thrive", "vibrant", "deep dive".
    3. TONE: Professional but conversational. Speak like a senior engineer talking to a colleague. Use active verbs.
    4. NO FLUFF: Start with a punchy opening about why you're interested in {company}'s specific tech or mission. Don't waste the first paragraph on "I am writing to apply..."
    5. STRUCTURE: 
       - Hook: Why this company?
       - The 'Meat': 2 specific examples of projects where you solved similar problems to the job requirements.
       - The 'Why Me': A unique skill (like the Figma/UI design mentioned earlier).
       - Sign-off.

    Write the letter now:
    """
    
    response = llm.invoke(prompt)
    return {
        "cover_letter": response.content, 
        "human_feedback": None,
        "status": "evaluating"
    }


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
workflow.add_node("evaluate", evaluate_output_node)

# Set Edges (The Flow)
workflow.set_entry_point("scrape_job")
workflow.add_edge("scrape_job", "analyze_requirements")
workflow.add_edge("analyze_requirements", "match_cv")
workflow.add_edge("match_cv", "generate_output")
workflow.add_edge("generate_output", "evaluate")
workflow.add_edge("evaluate", END)

# Compile
app_agent = workflow.compile()