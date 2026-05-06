import ast
import hashlib
import logging

logger = logging.getLogger(__name__)


def chunk_python_file_content(content: str, file_path: str = "<unknown>") -> list[dict]:
    try:
        file_tree = ast.parse(content)
    except SyntaxError as err:
        logger.warning("skipping file due to syntax error: path=%s error=%s", file_path, err)
        return []

    lines = content.splitlines()
    chunks = []

    # Walk only module-level definitions and class methods — avoids emitting nested
    # functions without their parent context, which would produce misleading index entries.
    nodes_to_index: list[ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef] = []
    for node in ast.iter_child_nodes(file_tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            nodes_to_index.append(node)
            if isinstance(node, ast.ClassDef):
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                        nodes_to_index.append(child)

    for node in nodes_to_index:
        start = node.lineno - 1
        end = node.end_lineno
        chunk_text = "\n".join(lines[start:end])
        chunks.append(
            {
                "text": chunk_text,
                "symbol": _get_signature(node),
                "type": type(node).__name__,
                "start_line": start,
                "end_line": end,
            }
        )
    return chunks


def gen_repo_id(owner: str, repo: str, branch: str) -> str:
    raw = f"{owner}:{repo}:{branch}".encode()
    return hashlib.sha256(raw).hexdigest()[:16]


def _get_signature(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> str:
    # ast.unparse reconstructs the full first line including async, type annotations,
    # *args, **kwargs, return type, and base classes — far more complete than manual extraction.
    return ast.unparse(node).splitlines()[0]


def is_py_file(item: dict) -> bool:
    if item.get("type", "") != "blob":
        return False
    file_path: str = item["path"]
    return file_path.endswith(".py")
