"""Submit one GPU job while reserving at most two campaign GPUs in total."""

import fcntl
import getpass
import json
import logging
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def count_reserved_gpus(queue_text):
    """Count running and pending campaign GPUs; reject ambiguous allocations."""
    count = 0
    for line in queue_text.splitlines():
        if not line.strip():
            continue
        fields = line.split("|")
        if len(fields) != 6:
            raise ValueError(f"Unexpected SLURM queue row: {line}")
        job_id, name, comment, _state, gres, nodes = fields
        if not (name.startswith("protease-") or comment == "protease_design"):
            continue
        if gres.lower() in {"n/a", "(null)", "", "none"}:
            if "gpu" in name:
                raise ValueError(f"GPU allocation not reported for campaign job {job_id}")
            continue
        matches = re.findall(r"(?:gres/)?gpu(?::[^,:=]+)?[:=](\d+)", gres)
        if not matches or not nodes.isdigit() or "[" in job_id or "]" in job_id:
            raise ValueError(f"Cannot safely count campaign GPU allocation: {line}")
        count += sum(map(int, matches)) * int(nodes)
    return count


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python submit_gpu.py SCRIPT_OR_MODULE_ARGS...")
    root = Path(__file__).resolve().parents[2]
    if str(root) != "/mnt/scratch/group/CX500059_DS1/blonnquist/proto-tools-moonshot":
        raise SystemExit("Submit only from the documented CoreHPC project mirror.")
    runtime = root / "data/corehpc/protease_design"
    runtime.mkdir(parents=True, exist_ok=True)
    (root / "logs").mkdir(exist_ok=True)
    with (runtime / "gpu_submission.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        queue = subprocess.check_output(
            ["squeue", "-h", "-u", getpass.getuser(), "-o", "%i|%j|%k|%T|%b|%D"], text=True,
        )
        reserved = count_reserved_gpus(queue)
        if reserved + 1 > 2:
            raise SystemExit(f"Two-GPU limit: {reserved} campaign GPUs already reserved.")
        command = ["sbatch", "--parsable", "protease_design/scripts/gpu.slurm", *sys.argv[1:]]
        job_id = subprocess.check_output(command, cwd=root, text=True).strip().split(";")[0]
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        with (runtime / "jobs.jsonl").open("a") as ledger:
            ledger.write(json.dumps({
                "job_id": job_id, "submitted_utc": datetime.now(timezone.utc).isoformat(),
                "commit": commit, "command": command, "requested_gpus": 1,
                "previously_reserved_gpus": reserved,
            }) + "\n")
        LOGGER.info("Submitted job %s; campaign reservation is now %s/2 GPUs", job_id, reserved + 1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()
