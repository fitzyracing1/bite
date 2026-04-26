import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SubmitResult:
    ok: bool
    message: str
    branch: str
    commit_hash: str


def auto_submit_changes(
    repo_dir: Path,
    branch: str,
    commit_message: str,
    push: bool,
) -> SubmitResult:
    try:
        subprocess.run(["git", "checkout", "-B", branch], cwd=repo_dir, check=True, capture_output=True, text=True)
        subprocess.run(["git", "add", "-A"], cwd=repo_dir, check=True, capture_output=True, text=True)
        commit_proc = subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=repo_dir,
            check=False,
            capture_output=True,
            text=True,
        )
        if commit_proc.returncode != 0 and "nothing to commit" not in commit_proc.stdout.lower():
            return SubmitResult(False, commit_proc.stderr.strip() or commit_proc.stdout.strip(), branch, "")

        rev = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        commit_hash = rev.stdout.strip()

        if push:
            push_proc = subprocess.run(
                ["git", "push", "-u", "origin", branch],
                cwd=repo_dir,
                check=False,
                capture_output=True,
                text=True,
            )
            if push_proc.returncode != 0:
                return SubmitResult(
                    False,
                    f"Committed locally but push failed: {push_proc.stderr.strip() or push_proc.stdout.strip()}",
                    branch,
                    commit_hash,
                )

        return SubmitResult(True, "Submission completed", branch, commit_hash)
    except Exception as exc:
        return SubmitResult(False, str(exc), branch, "")
