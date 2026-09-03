from rag.cv_processor import index_cv
import os

if __name__ == "__main__":
    # Update this with your actual filename
    cv_filename = "data/my_cv.pdf"
    
    if os.path.exists(cv_filename):
        index_cv(cv_filename)
    else:
        print(f"Error: Could not find {cv_filename}")