"""Record allocated compute hardware without running model inference."""

import json
import logging
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def main():
    if not os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("Run this hardware probe through SLURM.")
    gpu = subprocess.check_output([
        "nvidia-smi", "--query-gpu=name,driver_version,memory.total",
        "--format=csv,noheader,nounits",
    ], text=True).strip()
    result = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "job_id": os.environ["SLURM_JOB_ID"],
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "host": platform.node(), "python": platform.python_version(),
        "gpu_csv": gpu, "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "slurm_job_gpus": os.environ.get("SLURM_JOB_GPUS"),
    }
    output = Path("data/corehpc/protease_design/compute_probe.json")
    output.write_text(json.dumps(result, indent=2) + "\n")
    logging.info("Recorded compute probe: %s", result)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
