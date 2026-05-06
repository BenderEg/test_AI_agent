from src.app.utils.utils import chunk_python_file_content, gen_repo_id, is_py_file

# ── chunk_python_file_content ──────────────────────────────────────────────────

MIXED_CODE = """\
def greet(name: str) -> str:
    return f"Hello, {name}"


class Animal:
    def __init__(self, name: str) -> None:
        self.name = name

    def speak(self) -> str:
        return "..."
"""


def test_module_level_function_is_indexed():
    chunks = chunk_python_file_content(MIXED_CODE)
    symbols = [c["symbol"] for c in chunks]
    assert any("greet" in s for s in symbols)


def test_class_and_methods_indexed():
    chunks = chunk_python_file_content(MIXED_CODE)
    types = {c["type"] for c in chunks}
    assert "ClassDef" in types
    assert "FunctionDef" in types


def test_correct_chunk_count():
    # greet, Animal, Animal.__init__, Animal.speak
    assert len(chunk_python_file_content(MIXED_CODE)) == 4


def test_full_signature_with_type_annotations():
    code = "def process(items: list[str], timeout: float = 30.0) -> bool:\n    return True"
    chunks = chunk_python_file_content(code)
    symbol = chunks[0]["symbol"]
    assert "items: list[str]" in symbol
    assert "timeout: float=30.0" in symbol  # ast.unparse omits spaces around = in defaults
    assert "-> bool" in symbol


def test_async_function_signature():
    code = "async def fetch(*args: int, **kwargs: str) -> None:\n    pass"
    chunks = chunk_python_file_content(code)
    symbol = chunks[0]["symbol"]
    assert symbol.startswith("async def fetch")
    assert "*args: int" in symbol
    assert "**kwargs: str" in symbol


def test_class_signature_includes_base_classes():
    code = "class Foo(Base, Mixin):\n    pass"
    chunks = chunk_python_file_content(code)
    symbol = chunks[0]["symbol"]
    assert "Base" in symbol
    assert "Mixin" in symbol


def test_nested_function_is_not_indexed():
    code = "def outer():\n    def inner():\n        pass\n    return inner"
    chunks = chunk_python_file_content(code)
    assert len(chunks) == 1
    assert all("inner" not in c["symbol"] for c in chunks)


def test_syntax_error_returns_empty_list():
    assert chunk_python_file_content("def broken(: pass") == []


def test_empty_content_returns_empty_list():
    assert chunk_python_file_content("") == []


def test_chunk_text_contains_full_body():
    code = "def add(a: int, b: int) -> int:\n    return a + b"
    chunks = chunk_python_file_content(code)
    assert "return a + b" in chunks[0]["text"]


def test_chunk_has_expected_keys():
    code = "def foo():\n    pass"
    chunk = chunk_python_file_content(code)[0]
    assert {"text", "symbol", "type", "start_line", "end_line"} <= chunk.keys()


# ── gen_repo_id ────────────────────────────────────────────────────────────────


def test_gen_repo_id_is_deterministic():
    assert gen_repo_id("owner", "repo", "main") == gen_repo_id("owner", "repo", "main")


def test_gen_repo_id_different_branches_differ():
    assert gen_repo_id("owner", "repo", "main") != gen_repo_id("owner", "repo", "dev")


def test_gen_repo_id_different_repos_differ():
    assert gen_repo_id("alice", "foo", "main") != gen_repo_id("bob", "foo", "main")


def test_gen_repo_id_returns_16_char_hex():
    repo_id = gen_repo_id("owner", "repo", "main")
    assert len(repo_id) == 16
    assert all(c in "0123456789abcdef" for c in repo_id)


# ── is_py_file ─────────────────────────────────────────────────────────────────


def test_is_py_file_true_for_py_blob():
    assert is_py_file({"type": "blob", "path": "src/main.py"}) is True


def test_is_py_file_false_for_non_python_blob():
    assert is_py_file({"type": "blob", "path": "README.md"}) is False


def test_is_py_file_false_for_directory():
    assert is_py_file({"type": "tree", "path": "src"}) is False


def test_is_py_file_false_for_no_extension():
    assert is_py_file({"type": "blob", "path": "Makefile"}) is False
