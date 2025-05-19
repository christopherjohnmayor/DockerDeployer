import os
import git
from typing import Optional, List, Tuple

class GitManager:
    """
    Handles version control for DockerDeployer configuration files using GitPython.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        if not os.path.exists(repo_path):
            os.makedirs(repo_path, exist_ok=True)
        if not os.path.exists(os.path.join(repo_path, ".git")):
            self.repo = git.Repo.init(repo_path)
            self._initial_commit()
        else:
            self.repo = git.Repo(repo_path)

    def _initial_commit(self):
        # Create an initial commit if repo is empty
        with open(os.path.join(self.repo_path, ".gitkeep"), "w") as f:
            f.write("")
        self.repo.index.add([".gitkeep"])
        self.repo.index.commit("Initial commit: setup version control.")

    def commit_all(self, message: str) -> str:
        """
        Stage all changes and commit with the provided message.
        Returns the commit hash.
        """
        self.repo.git.add(A=True)
        if self.repo.is_dirty(index=True, working_tree=True, untracked_files=True):
            commit = self.repo.index.commit(message)
            return commit.hexsha
        return ""

    def get_history(self, max_count: int = 20) -> List[Tuple[str, str, str]]:
        """
        Returns a list of (commit_hash, author, message) for recent commits.
        """
        commits = list(self.repo.iter_commits('master', max_count=max_count))
        return [(c.hexsha, c.author.name, c.message.strip()) for c in commits]

    def get_diff(self, commit_a: str, commit_b: str) -> str:
        """
        Returns the diff between two commits.
        """
        diff = self.repo.git.diff(commit_a, commit_b)
        return diff

    def rollback_to(self, commit_hash: str) -> bool:
        """
        Resets the working tree and index to the specified commit.
        Returns True if successful.
        """
        try:
            self.repo.git.reset('--hard', commit_hash)
            return True
        except Exception as e:
            print(f"Rollback failed: {e}")
            return False

    def get_file_at_commit(self, file_path: str, commit_hash: str) -> Optional[str]:
        """
        Returns the contents of a file at a specific commit.
        """
        try:
            blob = self.repo.commit(commit_hash).tree / file_path
            return blob.data_stream.read().decode()
        except Exception:
            return None

    def get_current_commit(self) -> str:
        """
        Returns the current HEAD commit hash.
        """
        return self.repo.head.commit.hexsha
