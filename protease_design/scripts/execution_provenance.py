"""Identify analysis source separately from the installed runtime checkout."""

import shutil
import subprocess
from pathlib import Path


def revisions():
    git = shutil.which("git") or "/wynton/home/rotation/blonn25/.conda/envs/codex-node/bin/git"
    source = Path(__file__).resolve().parents[2]
    runtime = Path.cwd()
    def revision(directory):
        return subprocess.check_output([git, "-C", str(directory), "rev-parse", "HEAD"], text=True).strip()
    return {"commit": revision(source), "runtime_commit": revision(runtime),
            "script_checkout": str(source), "runtime_checkout": str(runtime)}
