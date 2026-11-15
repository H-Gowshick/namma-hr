
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from services.retrieval.chunking import chunk_pages
from services.retrieval.pdf_ingestion import extract_pdf


# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).parent

PDF_PATH = BASE_DIR / "docs" / "HR_POLICY.pdf"

CHROMA_PATH = BASE_DIR / "chroma_data"

COLLECTION_NAME = "epa_documents"

MODEL_NAME = "all-MiniLM-L6-v2"


# --------------------------------------------------
# 2. LOAD PDF
# --------------------------------------------------

print("\nSTEP 1: EXTRACTING PDF")

extracted_pages = extract_pdf(PDF_PATH)

if not extracted_pages:
    raise ValueError(
        "No text could be extracted from the PDF."
    )

print("\nExtracted pages:", len(extracted_pages))


# --------------------------------------------------
# 3. CREATE CHUNKS
# --------------------------------------------------

print("\nSTEP 2: CREATING CHUNKS")

chunks = chunk_pages(extracted_pages)

if not chunks:
    raise ValueError(
        "No chunks were created."
    )

print("Total chunks:", len(chunks))

for index, chunk in enumerate(chunks):

    print("\n" + "-" * 60)

    print("Chunk:", index + 1)

    print("Metadata:", chunk["metadata"])

    print("Text:", chunk["text"])


# --------------------------------------------------
# 4. LOAD EMBEDDING MODEL
# --------------------------------------------------

print("\nSTEP 3: LOADING EMBEDDING MODEL")

model = SentenceTransformer(MODEL_NAME)


# --------------------------------------------------
# 5. GENERATE EMBEDDINGS
# --------------------------------------------------

print("\nSTEP 4: GENERATING EMBEDDINGS")

texts = [
    chunk["text"]
    for chunk in chunks
]

embeddings = model.encode(
    texts,
    normalize_embeddings=True,
    show_progress_bar=True
)

print("Embedding count:", len(embeddings))

print("Embedding dimensions:", embeddings.shape[1])


# --------------------------------------------------
# 6. CONNECT TO CHROMADB
# --------------------------------------------------

print("\nSTEP 5: CONNECTING TO CHROMADB")

client = chromadb.PersistentClient(
    path=str(CHROMA_PATH)
)

collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    metadata={"hnsw:space": "cosine"}
)


# --------------------------------------------------
# 7. REMOVE OLD VERSIONS OF THIS SOURCE
# --------------------------------------------------

print("\nSTEP 6: REMOVING OLD PDF RECORDS")

collection.delete(
    where={
        "source": PDF_PATH.name
    }
)


# --------------------------------------------------
# 8. STORE CHUNKS AND EMBEDDINGS
# --------------------------------------------------

print("\nSTEP 7: STORING DOCUMENT CHUNKS")

ids = []

metadatas = []

for index, chunk in enumerate(chunks):

    metadata = chunk["metadata"]

    # Use a stable ID for this PDF, page and chunk
    chunk_id = (
        f"{PDF_PATH.name}_"
        f"page_{metadata['page']}_"
        f"chunk_{metadata['chunk_id']}"
    )

    ids.append(chunk_id)

    metadatas.append(metadata)


collection.add(

    ids=ids,

    documents=texts,

    embeddings=embeddings.tolist(),

    metadatas=metadatas

)


# --------------------------------------------------
# 9. DISPLAY FINAL RESULT
# --------------------------------------------------

print("\n" + "=" * 60)

print("PDF INDEXING COMPLETED")

print("=" * 60)

print("PDF:", PDF_PATH.name)

print("Pages extracted:", len(extracted_pages))

print("Chunks indexed:", len(chunks))

print("ChromaDB collection:", COLLECTION_NAME)

print("Total records:", collection.count())
