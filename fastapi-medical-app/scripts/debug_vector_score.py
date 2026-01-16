from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import sys
sys.path.insert(0, r'C:\Users\Admin\Desktop\drug_icd_mapping\fastapi-medical-app')
from app.core.utils import normalize_text

def debug_score():
    query = "Tra Hoang Bach Phong"
    # Simulated DB Content (from import script logic)
    ten = "Trà Hoàng Bạch Phong"
    hoat_chat = "Trà Hoàng Bạch Phong" # In CSV, hoat_chat might be same as name for herbal tea?
    sdk = "1031/2007/YTLĐ-CNTC"
    
    # Normalized versions
    norm_query = normalize_text(query)
    
    # Construct search_text based on run_import_datacore.py logic
    # f"{ten} {full_hoat_chat} {sdk}" -> verify CSV content first?
    # Assume CSV: ten="Trà ...", hoat_chat="...", sdk="..."
    
    # Let's try a few variations
    docs = [
        normalize_text(f"{ten} {ten} {sdk}"), # Import script logic: ten + hoat_chat + sdk
        normalize_text(f"{ten} {sdk}"),
        normalize_text(f"{ten}")
    ]
    
    vectorizer = TfidfVectorizer(token_pattern=r"(?u)\b\w+\b")
    tfidf_matrix = vectorizer.fit_transform(docs)
    query_vec = vectorizer.transform([norm_query])
    
    scores = cosine_similarity(query_vec, tfidf_matrix).flatten()
    
    print(f"Query (Norm): '{norm_query}'")
    for i, doc in enumerate(docs):
        print(f"Doc {i}: '{doc}' -> Score: {scores[i]:.4f}")

if __name__ == "__main__":
    debug_score()
