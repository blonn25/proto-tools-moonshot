"""Run upstream Boltz CLI in the existing managed environment, without forked loaders.

The persistent-worker pilot stalled with two idle loader children. This fallback
does not patch the library or its environment, and retains raw upstream outputs.
"""

import argparse
import hashlib
import json
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from execution_provenance import revisions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--msa-dir", type=Path, help="Staged custom single-chain A3M files named by design ID")
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20261002)
    parser.add_argument("--output", type=Path, default=Path("data/corehpc/protease_design/results/boltz2_cli"))
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID") or not os.environ.get("CUDA_VISIBLE_DEVICES"):
        raise SystemExit("Use the guarded GPU submission script.")
    if args.shards < 1 or not 0 <= args.shard < args.shards:
        raise SystemExit("Invalid shard.")
    from proto_tools.utils import ToolInstance

    executable = ToolInstance.get("boltz2").env_path / "bin/boltz"
    if not executable.is_file():
        raise SystemExit("Stage the managed Boltz environment on the login node first.")
    model = json.loads(Path("data/corehpc/protease_design/boltz2_model.json").read_text())
    cache = Path(model["cache"])
    if not (cache / "mols").is_dir() or any(not (cache / name).exists() for name in model["files"]):
        raise SystemExit("Incomplete offline weight staging.")
    records = json.loads(args.input.read_text())["records"]
    if args.only:
        if set(args.only) - {r["id"] for r in records}:
            raise SystemExit("Unknown ID.")
        records = [r for r in records if r["id"] in args.only]
    records = records[args.shard::args.shards]
    config = {"interface": "upstream CLI", "model": "boltz2", "use_msa": args.msa_dir is not None,
              "recycling_steps": 3, "sampling_steps": 200, "diffusion_samples": 1,
              "step_scale": 1.5, "num_workers": 0, "seed": args.seed,
              "devices": 1, "output_format": "pdb", "cpu_threads": 1}
    # The nvhpc module sets CC=nvc, which rejects Triton's GCC flags.
    compiler = Path("/usr/bin/gcc")
    cxx = Path("/usr/bin/g++")
    if not compiler.is_file() or not cxx.is_file():
        raise SystemExit("The validated system GCC/G++ compiler paths are unavailable.")
    config["compiler"] = subprocess.check_output([str(compiler), "--version"], text=True).splitlines()[0]
    cache_root = Path("data/corehpc/cache").resolve()
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
               MKL_NUM_THREADS="1", HF_HUB_OFFLINE="1", WANDB_MODE="offline",
               PYTHONUNBUFFERED="1", CC=str(compiler), CXX=str(cxx),
               TRITON_CACHE_DIR=str(cache_root / "triton"),
               TORCHINDUCTOR_CACHE_DIR=str(cache_root / "torchinductor"),
               CUDA_CACHE_PATH=str(cache_root / "cuda"))
    for key in ("TRITON_CACHE_DIR", "TORCHINDUCTOR_CACHE_DIR", "CUDA_CACHE_PATH"):
        Path(env[key]).mkdir(parents=True, exist_ok=True)
    base_config = config
    for item in records:
        config = dict(base_config)
        msa = args.msa_dir / f"{item['id']}.a3m" if args.msa_dir else None
        if msa is not None:
            from stage_domain_msas import read_a3m
            rows = read_a3m(msa, item["sequence"])
            config.update(msa_sha256=hashlib.sha256(msa.read_bytes()).hexdigest(), msa_rows=len(rows))
        output = args.output / item["id"]
        output.mkdir(parents=True, exist_ok=True)
        done = output / "run.json"
        if done.exists():
            previous = json.loads(done.read_text())
            if (previous["sequence_sha256"] != item["sequence_sha256"] or
                    previous["config"] != config or previous["model"]["revision"] != model["revision"] or
                    hashlib.sha256((output / "structure.pdb").read_bytes()).hexdigest() != previous["structure_sha256"]):
                raise ValueError("Existing prediction differs from input/configuration.")
            continue
        input_file = output / "input.yaml"
        input_file.write_text("version: 1\nsequences:\n  - protein:\n      id: A\n      sequence: " +
                              item["sequence"] + "\n      msa: " + (str(msa.resolve()) if msa else "empty") + "\n")
        raw = output / "raw"
        command = [str(executable), "predict", str(input_file.resolve()), "--out_dir", str(raw.resolve()),
                   "--cache", str(cache), "--model", "boltz2", "--devices", "1", "--accelerator", "gpu",
                   "--recycling_steps", "3", "--sampling_steps", "200", "--diffusion_samples", "1",
                   "--step_scale", "1.5", "--num_workers", "0", "--seed", str(args.seed),
                   "--output_format", "pdb", "--override"]
        logging.info("Starting %s with zero loader workers", item["id"])
        start = time.monotonic()
        subprocess.run(command, env=env, check=True, timeout=3600)
        prediction = raw / "boltz_results_input/predictions/input"
        pdb = prediction / "input_model_0.pdb"
        metrics = json.loads((prediction / "confidence_input_model_0.json").read_text())
        with np.load(prediction / "pae_input_model_0.npz") as archive:
            pae = archive["pae"].astype(float)
        if pae.shape != (item["length"], item["length"]) or not np.isfinite(pae).all():
            raise ValueError("Invalid PAE matrix.")
        metrics.update(pae=pae.tolist(), avg_pae=float(pae.mean()))
        shutil.copyfile(pdb, output / "structure.pdb")
        (output / "metrics.json").write_text(json.dumps(metrics) + "\n")
        result = {**revisions(), "job_id": os.environ["SLURM_JOB_ID"], "model": model,
                  "config": config, "command": command, "id": item["id"],
                  "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
                  "sequence_sha256": item["sequence_sha256"],
                  "structure_sha256": hashlib.sha256(pdb.read_bytes()).hexdigest(),
                  "completed_utc": datetime.now(timezone.utc).isoformat(),
                  "elapsed_seconds": time.monotonic() - start}
        temporary = output / "run.json.part"
        temporary.write_text(json.dumps(result, indent=2) + "\n")
        temporary.replace(done)
        logging.info("Completed %s in %.1f seconds", item["id"], result["elapsed_seconds"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
