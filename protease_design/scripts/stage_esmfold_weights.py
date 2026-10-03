"""Download weights and tokenizer files without loading the model."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import HfApi, snapshot_download


def main():
    if os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("Download weights on the internet-connected login node.")
    repository = "facebook/esmfold_v1"
    info = HfApi().model_info(repository)
    files = [item.rfilename for item in info.siblings]
    # Prefer safetensors if the repository supplies them, avoiding duplicate weights.
    weights = [name for name in files if name.endswith(".safetensors")]
    if not weights:
        weights = [name for name in files if name.endswith(".bin") and "pytorch_model" in name]
    if not weights:
        raise RuntimeError("No recognized model weights in the upstream repository.")
    allow = sorted(set(weights + [name for name in files if name.endswith((".json", ".txt", ".py"))]))
    snapshot = snapshot_download(repository, revision=info.sha, allow_patterns=allow, max_workers=2)
    # The repository wrapper loads the repository's default revision. Pin its
    # offline cache reference to the exact staged snapshot, without a network lookup.
    refs = Path(snapshot).parent.parent / "refs"
    refs.mkdir(exist_ok=True)
    temporary = refs / "main.part"
    temporary.write_text(info.sha)
    temporary.replace(refs / "main")
    result = {
        "repository": repository, "revision": info.sha, "snapshot": snapshot,
        "files": allow, "staged_utc": datetime.now(timezone.utc).isoformat(),
    }
    Path("data/corehpc/protease_design/esmfold_model.json").write_text(json.dumps(result, indent=2) + "\n")
    logging.info("Staged model revision %s", info.sha)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
