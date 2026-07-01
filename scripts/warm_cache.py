import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from langchain_huggingface import HuggingFaceEmbeddings
from src.rag.embeddings_rag import DEFAULT_EMBEDDING_MODEL

HuggingFaceEmbeddings(model_name=DEFAULT_EMBEDDING_MODEL)
print("Model cached.")
