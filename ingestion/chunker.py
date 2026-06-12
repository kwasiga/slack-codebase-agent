from pathlib import Path

SKIP_DIRS = {"node_modules", ".git", "__pycache__"}
suffix = {".py", ".ts", ".js"}

def walk_dir(repo_path):
    return [
        p
        for p in Path(repo_path).rglob("*")
        if p.is_file() and p.suffix in suffix
        and not any(part in p.parts for part in SKIP_DIRS)
    ]


def chunk_file(path, repo_root):
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    results = []
    chunk_size = 50
    overlap = 10
    step = chunk_size - overlap
    relative_path = str(path.relative_to(repo_root))
    for i in range(0, len(lines), step):
        chunk = lines[i: i + chunk_size]
        results.append({
            "file_path": relative_path,
            "start_line": i + 1,
            "end_line": i + len(chunk),
            "chunk_text": "".join(chunk)
        })
    return results


def chunk_repo(repo_path):
    repo_root = Path(repo_path)
    results = []
    for path in walk_dir(repo_root):
        results.extend(chunk_file(path, repo_root))
    return results
