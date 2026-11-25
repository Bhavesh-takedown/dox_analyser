# ==============================================================================
# groq_client.py — "The AI Brain"
#
# Calls Groq's API (LLaMA 3.3 70B) with retrieved context to generate answers.
# Uses prompt engineering to ground answers in the document and prevent hallucination.
# ==============================================================================

import os
from groq import Groq
from typing import List, Dict


def build_rag_prompt(question: str, context_chunks: List[Dict]) -> str:
    """
    Build the RAG prompt that gets sent to the LLM.
    Structure: INSTRUCTIONS + CONTEXT (retrieved chunks) + QUESTION
    """
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        context_parts.append(
            f"[Source {i} | Page {chunk['page_num']} | File: {chunk.get('filename', 'Unknown')}]\n"
            f"{chunk['text']}"
        )
    context = "\n\n".join(context_parts)

    prompt = f"""You are an expert AI analyst helping users understand business documents.

INSTRUCTIONS:
- Answer the question ONLY using the provided context below.
- If the context doesn't contain enough information, say: "I couldn't find sufficient information about this in the uploaded documents."
- Always cite your sources by mentioning the page number (e.g., "According to Page 3...").
- Be concise, professional, and precise.
- If the answer spans multiple pages, cite all relevant pages.

CONTEXT FROM DOCUMENTS:
{context}

USER QUESTION: {question}

YOUR ANSWER:"""

    return prompt


def ask_groq(
    question: str,
    context_chunks: List[Dict],
    model: str = "llama-3.3-70b-versatile"  # Updated July 2025: llama3-70b-8192 was decommissioned
) -> Dict:
    """
    Send a question + retrieved context to Groq's LLM and get a grounded answer.

    Args:
        question:       The user's question
        context_chunks: Retrieved chunks from VectorStore.search()
        model:          Groq model ID (llama-3.3-70b-versatile is the current recommended)

    Returns:
        {
            "answer":       "According to Page 3, revenue grew 20%...",
            "sources":      [3, 7],
            "model":        "llama-3.3-70b-versatile",
            "tokens_used":  342
        }
    """
    # ── Step 1: Get API key ────────────────────────────────────────────────────
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is not set! "
            "Add it to your .env file. "
            "Get a free key at: https://console.groq.com"
        )

    # ── Step 2: Create Groq client ─────────────────────────────────────────────
    client = Groq(api_key=api_key)

    # ── Step 3: Build RAG prompt ───────────────────────────────────────────────
    user_prompt = build_rag_prompt(question, context_chunks)

    # ── Step 4: Call Groq API ──────────────────────────────────────────────────
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise, expert document analyst. "
                    "You answer questions strictly from provided context. "
                    "You always cite page numbers and document names."
                )
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        temperature=0.1,   # Low randomness → factual, consistent answers
        max_tokens=1024,
    )

    # ── Step 5: Extract answer ────────────────────────────────────────────────
    answer = response.choices[0].message.content.strip()
    source_pages = sorted(set(chunk["page_num"] for chunk in context_chunks))

    return {
        "answer":      answer,
        "sources":     source_pages,
        "model":       model,
        "tokens_used": response.usage.total_tokens
    }
