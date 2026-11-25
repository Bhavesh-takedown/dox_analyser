# ==============================================================================
# pdf_processor.py — "The Document Reader"
#
# WHAT THIS FILE DOES:
#   Step 1 of the RAG pipeline.
#   - Opens a PDF file using PyMuPDF (imported as 'fitz')
#   - Reads the text from every page
#   - Splits that text into small "chunks" with slight overlap
#
# WHY CHUNKS?
#   An LLM has a limited "context window" — it can only read a fixed amount
#   of text at once. A 100-page report won't fit. So we break it into small
#   pieces (~200 words each) and only send the RELEVANT pieces to the LLM.
#
# WHY OVERLAP?
#   If we split a sentence right at a chunk boundary, we lose context.
#   Overlap (e.g., 30 words) means each chunk slightly repeats the end of the
#   previous chunk, so no meaning is lost at boundaries.
# ==============================================================================

import fitz  # PyMuPDF — the PDF reading library (pip name: pymupdf)
from typing import List, Dict


def extract_text_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Open a PDF file and extract all text, page by page.
    Tries multiple extraction strategies to handle different PDF types.

    Args:
        pdf_path: The file path to the PDF (e.g., "uploaded_docs/report.pdf")

    Returns:
        A list of dicts, one per page.

    Raises:
        ValueError: If the PDF is image-based (scanned) with no extractable text.
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)

    pages = []
    for page_num in range(total_pages):
        page = doc[page_num]

        # Strategy 1: Standard text extraction
        text = page.get_text().strip()

        # Strategy 2: If empty, try "blocks" mode (handles some unusual encodings)
        if not text:
            blocks = page.get_text("blocks")
            text = " ".join(
                b[4].strip() for b in blocks
                if isinstance(b[4], str) and b[4].strip()
            ).strip()

        # Strategy 3: Try "words" mode as last resort
        if not text:
            words = page.get_text("words")
            text = " ".join(w[4] for w in words if isinstance(w[4], str)).strip()

        if text:
            pages.append({
                "page_num": page_num + 1,
                "text": text
            })

    doc.close()

    # ── Critical: detect image-based (scanned) PDFs ───────────────────────────
    if len(pages) == 0 and total_pages > 0:
        raise ValueError(
            f"Could not extract any text from '{pdf_path}'. "
            f"This PDF appears to be image-based (scanned). "
            f"Only digitally-created PDFs with selectable text are supported. "
            f"Tip: If you can select/copy text in Adobe Reader, this PDF will work."
        )

    return pages


def chunk_text(
    pages: List[Dict],
    chunk_size: int = 200,   # Each chunk = ~200 words
    overlap: int = 30        # Each chunk shares 30 words with the previous one
) -> List[Dict]:
    """
    Split the extracted pages into small, overlapping text chunks.

    Why overlap? Imagine cutting a sentence in half — you lose meaning.
    Overlap ensures that context isn't lost at chunk boundaries.

    Args:
        pages:      List of page dicts from extract_text_from_pdf()
        chunk_size: Maximum number of WORDS per chunk
        overlap:    Number of words to repeat from the end of the previous chunk

    Returns:
        A list of chunk dicts:
        [
            {
                "chunk_id": 0,
                "page_num": 1,
                "text": "The first 200 words of page 1...",
                "word_start": 0
            },
            {
                "chunk_id": 1,
                "page_num": 1,
                "text": "Words 170–370 of page 1...",  # overlaps with chunk 0
                "word_start": 170
            },
            ...
        ]
    """
    chunks = []
    chunk_id = 0  # A global counter across all pages

    for page_data in pages:
        text = page_data["text"]
        page_num = page_data["page_num"]

        # Split the page text into individual words
        # e.g., "Hello world" → ["Hello", "world"]
        words = text.split()

        if not words:
            continue  # Skip empty pages

        # Slide a window of 'chunk_size' words across the page
        i = 0
        while i < len(words):
            # Grab words from position i to i+chunk_size
            chunk_words = words[i : i + chunk_size]
            chunk_text_str = " ".join(chunk_words)  # Rejoin words into a string

            if chunk_text_str.strip():  # Only add non-empty chunks
                chunks.append({
                    "chunk_id":   chunk_id,
                    "page_num":   page_num,
                    "text":       chunk_text_str,
                    "word_start": i           # Position in the original page text
                })
                chunk_id += 1

            # Move the window forward by (chunk_size - overlap)
            # e.g., 200 - 30 = 170 words forward each time
            i += chunk_size - overlap

    return chunks
