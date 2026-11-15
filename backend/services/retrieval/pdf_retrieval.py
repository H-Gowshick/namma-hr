import logging
import re
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

logger = logging.getLogger("app.retrieval")

# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
CHROMA_PATH = BASE_DIR / "chroma_data"

COLLECTION_NAME = "epa_documents"
MODEL_NAME = "all-MiniLM-L6-v2"

# --------------------------------------------------
# Load embedding model
# --------------------------------------------------

logger.info("Loading embedding model: %s", MODEL_NAME)

model = SentenceTransformer(MODEL_NAME)

# --------------------------------------------------
# Connect to persistent ChromaDB
# --------------------------------------------------

client = chromadb.PersistentClient(path=str(CHROMA_PATH))

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"},
)

logger.info(
    "ChromaDB collection loaded: %s (%s documents)",
    COLLECTION_NAME,
    collection.count(),
)

# --------------------------------------------------
# Keyword matching
# --------------------------------------------------

STOPWORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "what",
    "how",
    "many",
    "much",
    "can",
    "could",
    "does",
    "do",
    "of",
    "for",
    "to",
    "in",
    "on",
    "be",
    "with",
    "and",
    "or",
    "under",
    "this",
    "that",
    "it",
    "company",
    "policy",
}


# Multi-word HR phrases get an extra lexical boost.
HR_PHRASES = (
    "casual leave",
    "sick leave",
    "medical leave",
    "earned leave",
    "privilege leave",
    "privileged leave",
    "maternity leave",
    "paternity leave",
    "carry forward",
    "work from home",
    "pro rata",
    "pro-rated",
    "full & final",
    "maternity benefit",
)


def tokenize(text: str) -> set[str]:
    """Convert text into useful lowercase keywords."""

    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())

    return {word for word in words if word not in STOPWORDS}


def phrase_score(query: str, document: str) -> float:
    """Reward exact HR phrase overlap between query and document."""

    query_lower = query.lower()
    document_lower = document.lower()

    relevant_phrases = [
        phrase for phrase in HR_PHRASES if phrase in query_lower
    ]

    if not relevant_phrases:
        return 0.0

    matched = sum(
        1 for phrase in relevant_phrases if phrase in document_lower
    )

    return matched / len(relevant_phrases)


def keyword_score(query: str, document: str) -> float:
    """Measure query keyword and HR phrase overlap with a document."""

    query_words = tokenize(query)
    document_words = tokenize(document)

    word_overlap = 0.0

    if query_words:
        matched_words = query_words.intersection(document_words)
        word_overlap = len(matched_words) / len(query_words)

    phrase_overlap = phrase_score(query, document)

    if not query_words and phrase_overlap == 0.0:
        return 0.0

    # Prefer exact leave-type phrases while keeping normal keyword signal.
    return (0.7 * word_overlap) + (0.3 * phrase_overlap)


def chunk_identity(chunk: dict) -> str:
    """Stable identity for merging multi-query hits."""

    source = str(chunk.get("source", ""))
    page = str(chunk.get("page", ""))
    heading = str(chunk.get("heading", ""))
    text = str(chunk.get("text", ""))[:180]

    return f"{source}|{page}|{heading}|{text}"


# --------------------------------------------------
# Document retrieval
# --------------------------------------------------


def retrieve(query: str, top_k: int = 4) -> list[dict]:
    """
    Retrieve relevant PDF chunks using semantic
    similarity and keyword matching.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query cannot be empty.")

    if not isinstance(top_k, int) or not 1 <= top_k <= 10:
        raise ValueError("top_k must be an integer between 1 and 10.")

    query = query.strip()

    document_count = collection.count()

    if document_count == 0:
        logger.warning("ChromaDB collection contains no documents.")
        return []

    # Generate query embedding.
    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
    )

    # Retrieve additional candidates before reranking.
    candidate_count = min(document_count, max(top_k * 4, 8))

    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=candidate_count,
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents") or [[]]
    metadatas = results.get("metadatas") or [[]]
    distances = results.get("distances") or [[]]

    if not documents or not documents[0]:
        logger.warning("No matching document chunks were retrieved.")
        return []

    retrieved_chunks = []

    for document, metadata, distance in zip(
        documents[0],
        metadatas[0],
        distances[0],
    ):
        if not document:
            continue

        metadata = metadata or {}

        # ChromaDB cosine distance is converted into similarity.
        semantic_score = max(
            0.0,
            min(1.0, 1.0 - float(distance)),
        )

        lexical_score = keyword_score(query, document)

        # Hybrid relevance score.
        final_score = 0.60 * semantic_score + 0.40 * lexical_score

        retrieved_chunks.append(
            {
                "text": document,
                "source": metadata.get("source", "Unknown source"),
                "page": metadata.get("page", "Unknown page"),
                "heading": metadata.get("heading", "General"),
                "extraction_method": metadata.get(
                    "extraction_method",
                    "Unknown",
                ),
                "distance": float(distance),
                "similarity": semantic_score,
                "keyword_score": lexical_score,
                "relevance_score": final_score,
                "matched_query": query,
            }
        )

    # Sort by highest relevance score.
    retrieved_chunks.sort(
        key=lambda item: item["relevance_score"],
        reverse=True,
    )

    return retrieved_chunks[:top_k]


def retrieve_multi(queries: list[str], top_k: int = 4) -> list[dict]:
    """
    Retrieve with multiple English queries and merge unique chunks.

    Used for multilingual questions that expand into several
    focused English searches against the same English PDF index.
    """

    if not isinstance(top_k, int) or not 1 <= top_k <= 10:
        raise ValueError("top_k must be an integer between 1 and 10.")

    cleaned_queries: list[str] = []

    for query in queries:
        if not isinstance(query, str):
            continue

        value = query.strip()

        if value and value not in cleaned_queries:
            cleaned_queries.append(value)

    if not cleaned_queries:
        raise ValueError("At least one retrieval query is required.")

    merged: dict[str, dict] = {}

    # Pull a few extras per query, then keep global top_k.
    per_query_k = min(10, max(top_k, 3))

    for query in cleaned_queries:
        for chunk in retrieve(query, top_k=per_query_k):
            identity = chunk_identity(chunk)
            existing = merged.get(identity)

            if existing is None or chunk["relevance_score"] > existing["relevance_score"]:
                merged[identity] = chunk

    ranked = sorted(
        merged.values(),
        key=lambda item: item["relevance_score"],
        reverse=True,
    )

    return ranked[:top_k]
