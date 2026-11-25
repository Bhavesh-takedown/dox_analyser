# Changelog

All notable changes to **Dox** (Intelligent Document Q&A System) are documented here.

---

## [Unreleased]

## [0.4.0] - 2026-08-18

### Improved
- Enhanced error handling in RAG pipeline for edge cases with empty or malformed PDFs
- Refined chunking strategy comments for better developer readability
- Minor cleanup of unused imports and code style consistency across `app/` modules

---

## [0.3.0] - 2026-07-28

### Added
- CHANGELOG.md to track project history

### Improved
- Code readability and minor refactors across `rag_pipeline.py` and `streamlit_app.py`
- FAISS index persistence for faster re-runs without re-embedding

---

## [0.2.0] - 2026-07-24

### Added
- FAISS index persistence: save and load embeddings from disk
- Performance comparison table in README

---

## [0.1.0] - Initial Release

### Added
- Intelligent Document Q&A using RAG (Retrieval-Augmented Generation)
- PDF ingestion, chunking, and FAISS vector search
- Streamlit UI for interactive querying
