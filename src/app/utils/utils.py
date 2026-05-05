import ast
import hashlib


def chunk_python_file_content(content: str) -> list[dict]:
    try:
        file_tree = ast.parse(content)
    except SyntaxError:
        return []
    lines = content.splitlines()
    chunks = []
    for node in ast.walk(file_tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
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
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        args = [arg.arg for arg in node.args.args]
        return f"{node.name}({', '.join(args)})"
    return node.name


def is_py_file(item: dict) -> bool:
    if item.get("type", "") != "blob":
        return False
    file_path: str = item["path"]
    if file_path.endswith(".py"):
        return True
    return False
