from .vector_store import get_vector_store

def query_cv(query: str, cv_id: int, k: int = 2) -> str:
    if cv_id is None or cv_id == "":
        print("⚠️ Warning: No cv_id provided to retriever. Returning empty context.")
        return ""
    
    try:
        # 2. Force conversion only if we have a value
        target_id = int(cv_id) 
    except (ValueError, TypeError):
        print(f"⚠️ Warning: Invalid cv_id format: {cv_id}")
        return ""

    vectorstore = get_vector_store()
    
    # Use the filter with the forced integer
    results = vectorstore.similarity_search(
        query, 
        k=k, 
        filter={"cv_id": target_id} 
    )
    
    context = "\n---\n".join([res.page_content for res in results])
    return context

def delete_cv_from_index(cv_id: int):
    """Deletes all document chunks associated with a specific cv_id."""
    vectorstore = get_vector_store()

    # Chroma allows deleting by metadata filter
    vectorstore.delete(where={"cv_id": cv_id})
    print(f"--- Deleted CV {cv_id} from ChromaDB ---")