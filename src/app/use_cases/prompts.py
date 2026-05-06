# Character-based truncation is used instead of a tokenizer to avoid adding a heavy
# dependency (tiktoken/transformers tokenizer). At ~4 chars/token, 8000 chars fits
# comfortably within the 2k-32k context windows of all supported local models.
MAX_CONTEXT_CHARS = 8000
MAX_CHUNK_CHARS = 2000


def build_context(results: list[dict]) -> tuple[str, bool]:
    """Returns (context_string, was_truncated)."""
    parts: list[str] = []
    total = 0
    for r in results:
        code = r["code"][:MAX_CHUNK_CHARS]
        chunk = f"{r['symbol']}:\n{code}"
        if total + len(chunk) > MAX_CONTEXT_CHARS:
            return "\n\n".join(parts), True
        parts.append(chunk)
        total += len(chunk)
    return "\n\n".join(parts), False


def build_prompt(query: str, context: str, truncated: bool = False) -> str:
    truncation_note = "\n[Note: context was truncated due to length]" if truncated else ""
    return f"""
        You are a senior backend engineer.

        Answer the question based ONLY on the provided code.

        Question:
        {query}

        Context:
        {context}{truncation_note}

        Answer clearly and concisely.
        Do not use irrelevant context to reply.
        If possible provide relevant code examples from context.
    """


def rewrite_prompt(query: str) -> str:
    return f"""
        You are helping to search a codebase.

        User query:
        {query}

        Rewrite it into a more detailed search query
        that would help find relevant code.

        Do not add explanation of how you rewrite the query. Return the rewritten query only!
    """
