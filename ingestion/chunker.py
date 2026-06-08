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


def chunk_file(path):
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    results = []
    chunk_size = 50
    overlap = 10
    step = chunk_size - overlap
    for i in range(0, len(lines), step):
        chunk = lines[i: i + chunk_size]  # slice with i and chunk_size
        results.append({
            "file_path": str(path),
            "start_line": i + 1,
            "end_line": i + len(chunk),
            "chunk_text": "".join(chunk)
        })
    return results


def chunk_repo(repo_path):
    results = []
    directories = walk_dir(repo_path)
    for path in directories:
        results.extend(chunk_file(path))

    return results