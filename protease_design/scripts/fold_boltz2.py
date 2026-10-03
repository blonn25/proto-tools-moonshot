"""Independent single-sequence Boltz-2 validation under guarded GPU SLURM jobs."""

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
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20261002)
    parser.add_argument("--output", type=Path, default=Path("data/corehpc/protease_design/results/boltz2"))
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID") or not os.environ.get("CUDA_VISIBLE_DEVICES"):
        raise SystemExit("Use the guarded GPU submission script.")
    if args.shards < 1 or not 0 <= args.shard < args.shards:
        raise SystemExit("Invalid shard selection.")
    records = json.loads(args.input.read_text())["records"]
    if args.only:
        unknown = set(args.only) - {r["id"] for r in records}
        if unknown:
            raise SystemExit(f"Unknown IDs: {unknown}")
        records = [r for r in records if r["id"] in args.only]
    records = records[args.shard::args.shards]
    model = json.loads(Path("data/corehpc/protease_design/boltz2_model.json").read_text())
    cache = Path(model["cache"])
    if not (cache / "mols").is_dir() or any(not (cache / name).exists() for name in model["files"]):
        raise SystemExit("Boltz-2 staging is incomplete; do not download on compute nodes.")
    from proto_tools import Boltz2Config, Boltz2Input, run_boltz2
    from proto_tools.utils import ToolInstance

    # Single sequence is explicit: no remote MSA requests or invented fusion MSA.
    config = Boltz2Config(device="cuda:0", use_msa=False, recycling_steps=3,
                          sampling_steps=200, diffusion_samples=1, num_workers=2,
                          include_pae_matrix=True, seed=args.seed, timeout=3600, verbose=True)
    provenance = {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                  "job_id": os.environ["SLURM_JOB_ID"], "model": model,
                  "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
                  "config": config.model_dump(mode="json")}
    args.output.mkdir(parents=True, exist_ok=True)
    with ToolInstance.persist_tool("boltz2", env_overrides={"HF_HUB_OFFLINE": "1", "WANDB_MODE": "offline"}):
        for item in records:
            output = args.output / item["id"]
            output.mkdir(exist_ok=True)
            done = output / "run.json"
            if done.exists():
                previous = json.loads(done.read_text())
                if (previous["sequence_sha256"] != item["sequence_sha256"] or
                        previous["config"] != provenance["config"] or
                        previous["model"]["revision"] != model["revision"] or
                        hashlib.sha256((output / "structure.pdb").read_bytes()).hexdigest()
                        != previous["structure_sha256"]):
                    raise RuntimeError(f"Existing result does not match: {output}")
                continue
            start = time.monotonic()
            result = run_boltz2(Boltz2Input(complexes=[item["sequence"]]), config)
            if len(result.structures) != 1:
                raise RuntimeError("Expected exactly one Boltz-2 structure.")
            structure = result.structures[0]
            structure.write_pdb(output / "structure.pdb")
            structure.write_cif(output / "structure.cif")
            (output / "metrics.json").write_text(json.dumps(structure.metrics.model_dump(mode="json")) + "\n")
            record = {**provenance, "id": item["id"], "sequence_sha256": item["sequence_sha256"],
                      "elapsed_seconds": time.monotonic() - start,
                      "completed_utc": datetime.now(timezone.utc).isoformat(),
                      "structure_sha256": hashlib.sha256((output / "structure.pdb").read_bytes()).hexdigest()}
            temporary = output / "run.json.part"
            temporary.write_text(json.dumps(record, indent=2) + "\n")
            temporary.replace(done)
            logging.info("Completed %s in %.1f seconds", item["id"], record["elapsed_seconds"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
