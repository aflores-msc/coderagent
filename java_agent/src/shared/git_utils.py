import os
from git import Repo

def get_staged_files(repo_path: str) -> list[str]:
    """Returns a list of .java files currently staged in the given repo."""
    try:
        repo = Repo(repo_path)
        # diff("HEAD") compares staging area to last commit
        staged = [item.a_path for item in repo.index.diff("HEAD")]
        # Handle case for new repos (no commits yet)
        if not staged:
            staged = [item.a_path for item in repo.index.diff(None, staged=True)]
        return [f for f in staged if f.endswith(".java")]
    except Exception as e:
        return []

def read_file(repo_path: str, filepath: str) -> str:
    """Reads the content of a specific file in the repo."""
    full_path = os.path.join(repo_path, filepath)
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"
