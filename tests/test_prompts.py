from src.app.use_cases.prompts import (
    MAX_CHUNK_CHARS,
    MAX_CONTEXT_CHARS,
    build_context,
    build_prompt,
    rewrite_prompt,
)


def _result(symbol: str = "func", code: str = "pass") -> dict:
    return {"symbol": symbol, "code": code, "file": "f.py", "score": 0.9, "rerank_score": None}


# ── build_context ──────────────────────────────────────────────────────────────


def test_build_context_empty_results():
    context, truncated = build_context([])
    assert context == ""
    assert truncated is False


def test_build_context_short_content_not_truncated():
    results = [_result("foo", "x = 1"), _result("bar", "y = 2")]
    context, truncated = build_context(results)
    assert truncated is False
    assert "foo" in context
    assert "bar" in context


def test_build_context_includes_symbol_and_code():
    result = _result("my_func", "return 42")
    context, _ = build_context([result])
    assert "my_func" in context
    assert "return 42" in context


def test_build_context_chunk_code_capped_at_max_chunk_chars():
    # Use unique markers so substring checks are unambiguous
    prefix = "START_" + "a" * (MAX_CHUNK_CHARS - 10) + "_MID"
    suffix = "_END" + "b" * 500
    long_code = prefix + suffix
    result = _result("big_func", long_code)
    context, _ = build_context([result])
    assert "START_" in context
    assert "_END" not in context  # suffix beyond MAX_CHUNK_CHARS is dropped


def test_build_context_truncated_when_total_exceeds_limit():
    # 20 chunks × 1 000 chars each = 20 000 chars, well over MAX_CONTEXT_CHARS (8 000)
    results = [_result(f"func_{i}", "x" * 1000) for i in range(20)]
    context, truncated = build_context(results)
    assert truncated is True
    assert len(context) <= MAX_CONTEXT_CHARS + 200  # small tolerance for symbol headers


def test_build_context_not_truncated_when_just_under_limit():
    # Single small chunk well within the limit
    result = _result("tiny", "pass")
    context, truncated = build_context([result])
    assert truncated is False


def test_build_context_chunks_separated_by_blank_lines():
    results = [_result("a", "1"), _result("b", "2")]
    context, _ = build_context(results)
    assert "\n\n" in context


# ── build_prompt ───────────────────────────────────────────────────────────────


def test_build_prompt_contains_query():
    prompt = build_prompt("what is X?", "some code")
    assert "what is X?" in prompt


def test_build_prompt_contains_context():
    prompt = build_prompt("query", "some code here")
    assert "some code here" in prompt


def test_build_prompt_no_truncation_note_by_default():
    prompt = build_prompt("query", "context")
    assert "truncated" not in prompt.lower()


def test_build_prompt_truncation_note_when_flagged():
    prompt = build_prompt("query", "context", truncated=True)
    assert "truncated" in prompt.lower()


# ── rewrite_prompt ─────────────────────────────────────────────────────────────


def test_rewrite_prompt_contains_original_query():
    prompt = rewrite_prompt("find all async functions")
    assert "find all async functions" in prompt


def test_rewrite_prompt_no_typo_rewrited():
    prompt = rewrite_prompt("test query")
    assert "rewrited" not in prompt


def test_rewrite_prompt_contains_rewritten():
    prompt = rewrite_prompt("test query")
    assert "rewritten" in prompt
