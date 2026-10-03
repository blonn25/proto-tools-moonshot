"""Fold candidate/control sequences with the managed ESMFold wrapper under SLURM."""

import argparse
import hashlib
import json
import logging
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--recycles", type=int, default=4)
    parser.add_argument("--output", type=Path, default=Path("data/corehpc/protease_design/results/esmfold"))
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID") or not os.environ.get("CUDA_VISIBLE_DEVICES"):
        raise SystemExit("Run through the guarded CoreHPC GPU submission script.")
    if args.shards < 1 or not 0 <= args.shard < args.shards:
        raise SystemExit("Invalid shard selection.")
    records = json.loads(args.input.read_text())["records"]
    if args.only:
        unknown = set(args.only) - {item["id"] for item in records}
        if unknown:
            raise SystemExit(f"Unknown sequence IDs: {sorted(unknown)}")
        records = [item for item in records if item["id"] in args.only]
    records = records[args.shard::args.shards]
    model = json.loads(Path("data/corehpc/protease_design/esmfold_model.json").read_text())
    reference = Path(model["snapshot"]).parent.parent / "refs/main"
    if reference.read_text().strip() != model["revision"]:
        raise RuntimeError("Offline model revision differs from staging provenance.")

    from proto_tools import ESMFoldConfig, ESMFoldInput, run_esmfold
    from proto_tools.utils import ToolInstance

    config = ESMFoldConfig(device="cuda:0", num_recycles=args.recycles,
                           max_batch_residues=800, include_pae_matrix=True, verbose=True)
    args.output.mkdir(parents=True, exist_ok=True)
    provenance = {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "job_id": os.environ["SLURM_JOB_ID"], "model": model,
        "config": config.model_dump(mode="json"),
        "input_file": str(args.input),
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
    }
    offline = {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
    with ToolInstance.persist_tool("esmfold", env_overrides=offline):
        for item in records:
            output = args.output / item["id"]
            output.mkdir(exist_ok=True)
            done = output / "run.json"
            if done.exists():
                previous = json.loads(done.read_text())
                if previous["sequence_sha256"] != item["sequence_sha256"] or previous["config"] != provenance["config"]:
                    raise RuntimeError(f"Existing result disagrees with current input/config: {output}")
                logging.info("Retaining completed result %s", item["id"])
                continue
            started = time.monotonic()
            result = run_esmfold(ESMFoldInput(complexes=[item["sequence"]]), config)
            if len(result.structures) != 1:
                raise RuntimeError(f"Expected one structure for {item['id']}")
            structure = result.structures[0]
            structure.write_pdb(output / "structure.pdb")
            structure.write_cif(output / "structure.cif")
            metrics = structure.metrics.model_dump(mode="json") if structure.metrics else {}
            (output / "metrics.json").write_text(json.dumps(metrics) + "\n")
            record = {**provenance, "id": item["id"], "sequence_sha256": item["sequence_sha256"],
                      "completed_utc": datetime.now(timezone.utc).isoformat(),
                      "elapsed_seconds": time.monotonic() - started,
                      "structure_sha256": hashlib.sha256((output / "structure.pdb").read_bytes()).hexdigest()}
            temporary = output / "run.json.part"
            temporary.write_text(json.dumps(record, indent=2) + "\n")
            temporary.replace(done)
            logging.info("Completed %s in %.1f seconds", item["id"], record["elapsed_seconds"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
