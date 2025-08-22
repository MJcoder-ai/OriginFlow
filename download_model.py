import logging
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model_name = "sentence-transformers/all-MiniLM-L6-v2"

logger.info(f"Downloading and caching model: {model_name}")
try:
    SentenceTransformer(model_name)
    logger.info("Model downloaded successfully.")
except Exception as e:
    logger.error(f"An error occurred during model download: {e}")