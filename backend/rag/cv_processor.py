import pdfplumber
import re
from langchain_core.documents import Document
from rag.vector_store import get_vector_store

def extract_text_from_pdf(pdf_path: str) -> str:
    full_text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            full_text += page.extract_text() + "\n"
    return full_text

def chunk_cv_by_sections(text: str) -> list[Document]:
    # Common CV headers to split by
    headers = ["EXPERIENCE", "SKILLS", "PROJECTS", "EDUCATION", "SUMMARY", "CERTIFICATIONS", "LANGUAGES"]
    
    # Create a regex pattern to find headers (case insensitive)
    pattern = r'\b(' + '|'.join(headers) + r')\b'
    
    # Split text while keeping the headers
    sections = re.split(pattern, text, flags=re.IGNORECASE)
    
    chunks = []
    # If there is introductory text before the first header
    if sections[0].strip():
        chunks.append(Document(page_content=sections[0].strip(), metadata={"section": "intro"}))
    
    # Iterate through the matches and pair headers with their content
    for i in range(1, len(sections), 2):
        header = sections[i].strip()
        content = sections[i+1].strip() if i+1 < len(sections) else ""
        combined_text = f"{header}\n{content}"
        chunks.append(Document(page_content=combined_text, metadata={"section": header.lower()}))
        
    return chunks

def index_cv(pdf_path: str):
    print(f"--- Extracting text from {pdf_path} ---")
    raw_text = extract_text_from_pdf(pdf_path)
    
    print("--- Chunking CV into sections ---")
    chunks = chunk_cv_by_sections(raw_text)
    
    print(f"--- Saving {len(chunks)} sections to ChromaDB ---")
    vector_store = get_vector_store()
    vector_store.add_documents(chunks)
    print("--- CV Indexing Complete! ---")