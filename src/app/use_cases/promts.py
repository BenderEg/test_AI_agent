def build_context(results: list[dict]):
    return "\n\n".join(
        f"{r['symbol']}:\n{r['code']}"
        for r in results
    )

def build_prompt(query: str, context: str):
    return f"""
        You are a senior backend engineer.

        Answer the question based ONLY on the provided code.

        Question:
        {query}

        Context:
        {context}

        Answer clearly and concisely.
        Do not use irrelevant context to reply.
        if possible provide relevant code examples from context.
    """

def rewrite_prompt(query: str):
    return f"""
        You are helping to search a codebase.

        User query:
        {query}

        Rewrite it into a more detailed search query
        that would help find relevant code.

        Do not add explanation how you rewrite qyery. return rewrited query only!
    """