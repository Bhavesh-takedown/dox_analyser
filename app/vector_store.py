# ==============================================================================
# vector_store.py — "The Smart Library Index"
#
# WHAT THIS FILE DOES:
#   Step 2 of the RAG pipeline.
#   - Converts text chunks into "embeddings" (lists of numbers that capture meaning)
#   - Stores those embeddings in a FAISS index (a lightning-fast similarity search DB)
#   - When a user asks a question, converts the question to an embedding too,
#     then finds the chunks whose embeddings are CLOSEST to the question's embedding
#
# ANALOGY:
#   Think of each text chunk as a point in a giant 384-dimensional space.
#   Similar chunks (about the same topic) cluster near each other.
#   A question also becomes a point. FAISS finds the nearest chunk-points.
#
# WHY sentence-transformers?
#   It's a free, local model that converts any text into a 384-number vector.
#   "Revenue grew 20%" and "Sales increased by a fifth" will have very similar
#   vectors — the model understands MEANING, not just keywords.
#
# WHY FAISS?
#   Built by Facebook AI. Can search through millions of vectors in milliseconds.
#   We use IndexFlatL2 — it compares distances using L2 (Euclidean) distance.
# ==============================================================================

import faiss                        # Facebook AI Similarity Search
import numpy as np                  # Numerical arrays (FAISS needs numpy arrays)
import pickle                       # Save/load Python objects to disk
from sentence_transformers import SentenceTransformer  # Local embedding model
from typing import List, Dict, Optional


class VectorStore:
    """
    A class that wraps FAISS + sentence-transformers into a simple interface.

    Usage:
        store = VectorStore()
        store.add_chunks(my_chunks)               # Index documents
        results = store.search("What is revenue?") # Find relevant chunks
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the vector store.

        Args:
            model_name: The sentence-transformer model to use.
                        "all-MiniLM-L6-v2" is small (80MB), fast, and accurate.
                        It outputs 384-dimensional embeddings.
        """
        print(f"[VectorStore] Loading embedding model: {model_name}")
        # Load the embedding model — downloads on first run (~80MB), cached after
        self.model = SentenceTransformer(model_name)

        self.index: Optional[faiss.Index] = None  # FAISS index (None until first chunk added)
        self.chunks: List[Dict] = []              # Parallel list of chunk metadata
        self.dimension = 384  # Output size of all-MiniLM-L6-v2

    def add_chunks(self, chunks: List[Dict]) -> None:
        """
        Embed a list of text chunks and add them to the FAISS index.

        Args:
            chunks: List of chunk dicts from pdf_processor.chunk_text()
                    Each must have a "text" key.

        How it works:
            1. Extract just the text strings from each chunk
            2. Send all texts to sentence-transformers → get 384-number vectors
            3. Add those vectors to the FAISS index
            4. Store the chunk metadata in self.chunks (parallel to the index)
        """
        if not chunks:
            return

        # Step 1: Extract text from each chunk dict
        # e.g., ["Revenue grew 20% in Q3", "The CEO announced...", ...]
        texts = [chunk["text"] for chunk in chunks]

        print(f"[VectorStore] Embedding {len(texts)} chunks...")

        # Step 2: Convert texts → embeddings (384-dim float arrays)
        # show_progress_bar=True prints a progress bar in the terminal
        embeddings = self.model.encode(texts, show_progress_bar=True)

        # Step 3: Convert to float32 numpy array (FAISS requirement)
        embeddings = np.array(embeddings, dtype=np.float32)

        # Step 4: Create the FAISS index if it doesn't exist yet
        if self.index is None:
            # IndexFlatL2 = brute-force L2 distance search (most accurate)
            self.index = faiss.IndexFlatL2(self.dimension)

        # Step 5: Add embeddings to FAISS
        # FAISS assigns integer IDs (0, 1, 2, ...) automatically
        self.index.add(embeddings)

        # Step 6: Store chunk metadata so we can retrieve it later
        # The order in self.chunks matches the FAISS integer IDs
        self.chunks.extend(chunks)

        print(f"[VectorStore] Index now has {self.index.ntotal} vectors.")

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Find the top-k most relevant chunks for a given query.

        Args:
            query: The user's question, e.g., "What is the company's revenue?"
            top_k: How many chunks to retrieve (more = more context, but slower)

        Returns:
            List of chunk dicts, sorted by relevance (most relevant first).
            Each chunk gets an extra "score" key (lower = more similar in L2).

        How it works:
            1. Embed the query using the same model
            2. FAISS searches for the top_k nearest vectors to the query vector
            3. Return the corresponding chunk metadata
        """
        # Guard: if no documents have been indexed yet, return empty
        if self.index is None or len(self.chunks) == 0:
            return []

        # Step 1: Embed the query (same model as the chunks)
        query_embedding = self.model.encode([query])  # Returns shape (1, 384)
        query_embedding = np.array(query_embedding, dtype=np.float32)

        # Step 2: FAISS search
        # Returns two arrays:
        #   distances[0] = L2 distances to the top_k nearest vectors
        #   indices[0]   = FAISS integer IDs of the top_k nearest vectors
        distances, indices = self.index.search(query_embedding, top_k)

        # Step 3: Build the result list
        results = []
        for i, idx in enumerate(indices[0]):
            if idx == -1:              # FAISS returns -1 if fewer than top_k results
                continue
            if idx >= len(self.chunks):  # Safety check
                continue

            chunk = self.chunks[idx].copy()  # Copy so we don't mutate the original
            chunk["score"] = float(distances[0][i])  # Add the distance score
            results.append(chunk)

        return results  # Already sorted by FAISS (lowest distance first)

    def clear(self) -> None:
        """Reset the vector store — removes all indexed documents."""
        self.index = None
        self.chunks = []
        print("[VectorStore] Cleared all documents.")

    @property
    def total_chunks(self) -> int:
        """How many chunks are currently indexed."""
        return len(self.chunks)

    @property
    def is_empty(self) -> bool:
        """True if no documents have been indexed."""
        return self.index is None or len(self.chunks) == 0
