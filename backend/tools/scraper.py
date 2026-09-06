import httpx
from bs4 import BeautifulSoup
from typing import Dict, Optional

def scrape_job_posting(url: str) -> Dict[str, Optional[str]]:
    """
    Fetches HTML from a URL and extracts raw text.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
    try:
        response = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove script and style elements that contain junk text
        for script_or_style in soup(["script", "style", "header", "footer", "nav"]):
            script_or_style.decompose()

        # Get text and clean up whitespace
        raw_text = soup.get_text(separator=" ")
        lines = (line.strip() for line in raw_text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_text = "\n".join(chunk for chunk in chunks if chunk)

        return {
            "success": True,
            "raw_text": clean_text,
            "url": url
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "raw_text": None,
            "url": url
        }