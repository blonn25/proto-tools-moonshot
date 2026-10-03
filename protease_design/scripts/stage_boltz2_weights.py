"""Stage pinned Boltz-2 files, including upstream-required unused affinity weights."""

import hashlib
import json
import logging
import os
import tarfile
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download


def main():
    if os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("Network staging must run on the login node.")
    repository = "boltz-community/boltz-2"
    revision = HfApi().model_info(repository).sha
    cache = Path(os.environ["PROTO_MODEL_CACHE"]) / "boltz2"
    cache.mkdir(parents=True, exist_ok=True)
    files = {}
    for name in ("boltz2_conf.ckpt", "boltz2_aff.ckpt", "mols.tar"):
        source = Path(hf_hub_download(repository, name, revision=revision))
        destination = cache / name
        if not destination.exists():
            destination.symlink_to(source)
        elif destination.resolve() != source.resolve():
            raise RuntimeError(f"Existing Boltz-2 file differs from pinned snapshot: {destination}")
        with source.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        files[name] = {"sha256": digest, "bytes": source.stat().st_size}
    if not (cache / "mols").exists():
        with tarfile.open(cache / "mols.tar") as archive:
            archive.extractall(cache, filter="data")
    result = {"repository": repository, "revision": revision, "cache": str(cache), "files": files,
              "staged_utc": datetime.now(timezone.utc).isoformat()}
    Path("data/corehpc/protease_design/boltz2_model.json").write_text(json.dumps(result, indent=2) + "\n")
    logging.info("Staged Boltz-2 revision %s", revision)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
