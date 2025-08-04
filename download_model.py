from sentence_transformers import SentenceTransformer

model_name = "sentence-transformers/all-MiniLM-L6-v2"

print(f"Downloading and caching model: {model_name}")
try:
    SentenceTransformer(model_name)
    print("Model downloaded successfully.")
except Exception as e:
    print(f"An error occurred during model download: {e}")