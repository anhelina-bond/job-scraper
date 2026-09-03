from .vector_store import get_vector_store

def query_cv(query: str, k: int = 3):
    vector_store = get_vector_store()
    # Search for top 'k' most relevant chunks
    results = vector_store.similarity_search(query, k=k)
    
    # Format results as a single string for the LLM
    context = "\n\n".join([doc.page_content for doc in results])
    return context