"""Assemble and compile the paper with project-local Tectonic and cached fonts."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-downloads", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    runtime = root / "data/corehpc/protease_design"
    source = root / "protease_design/manuscript"
    staged = runtime / "manuscript_source"
    build = runtime / "manuscript_build"
    staged.mkdir(parents=True, exist_ok=True)
    build.mkdir(parents=True, exist_ok=True)
    inputs = {}
    for suffix in ("*.tex", "*.bib", "*.sty", "*.bst"):
        for path in source.glob(suffix):
            shutil.copy2(path, staged / path.name)
            inputs[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (staged / "figures").mkdir(exist_ok=True)
    for path in (runtime / "results/figures").glob("*.pdf"):
        shutil.copy2(path, staged / "figures" / path.name)
        inputs[f"figures/{path.name}"] = hashlib.sha256(path.read_bytes()).hexdigest()
    compiler = runtime / "tex/tectonic"
    command = [str(compiler), "--keep-logs", "--keep-intermediates", "--outdir", str(build)]
    if not args.allow_downloads:
        command.append("--only-cached")
    command.append(str(staged / "main.tex"))
    env = dict(os.environ, XDG_CACHE_HOME=str(root / "data/corehpc/cache"))
    with (root / "logs/protease_manuscript_build.log").open("w") as log:
        subprocess.run(command, cwd=staged, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    git = shutil.which("git") or "/wynton/home/rotation/blonn25/.conda/envs/codex-node/bin/git"
    record = {"source_commit": subprocess.check_output([git, "rev-parse", "HEAD"], cwd=root, text=True).strip(),
              "source_has_local_changes": bool(subprocess.check_output(
                  [git, "status", "--porcelain", "--", "protease_design/manuscript"], cwd=root, text=True).strip()),
              "inputs_sha256": inputs, "compiler_sha256": hashlib.sha256(compiler.read_bytes()).hexdigest(),
              "pdf_sha256": hashlib.sha256((build / "main.pdf").read_bytes()).hexdigest(),
              "command": command}
    (build / "build_provenance.json").write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
