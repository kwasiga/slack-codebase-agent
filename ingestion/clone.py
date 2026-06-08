from pathlib import Path
import shutil
import tempfile
from git import Repo


def clone_repo(repo_url):
    path = tempfile.mkdtemp()
    try:
        Repo.clone_from(repo_url, path)
    except Exception:
        shutil.rmtree(path, ignore_errors=True)
        raise
    return Path(path)
