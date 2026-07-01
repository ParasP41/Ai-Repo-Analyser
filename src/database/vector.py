from pymongo import ASCENDING

from src.database.index import db


VECTOR_COLLECTION_NAME = "repo_vectors"
VECTOR_DIMENSIONS = 384

repo_vectors = db[VECTOR_COLLECTION_NAME]


def ensure_vector_indexes():
    repo_vectors.create_index([
        ("user_id", ASCENDING),
        ("repository_id", ASCENDING),
    ])
    repo_vectors.create_index([("repository_id", ASCENDING)])
    repo_vectors.create_index([("metadata.path", ASCENDING)])
    return repo_vectors
