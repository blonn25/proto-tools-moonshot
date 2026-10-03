"""Prepare a managed CUDA Boltz-2 environment without loading a prediction model."""

import logging
import os
import subprocess
from pathlib import Path


def main():
    root = Path.cwd()
    if os.environ.get("SLURM_JOB_ID") or str(root) != "/mnt/scratch/group/CX500059_DS1/blonnquist/proto-tools-moonshot":
        raise SystemExit("Run on the CoreHPC login node from the project mirror.")
    if not os.environ.get("PROTO_HOME", "").startswith(str(root) + "/"):
        raise SystemExit("Source corehpc_env.sh first.")
    from proto_tools.utils import ToolInstance

    definition = root / "data/corehpc/protease_design/env_defs/boltz2"
    if not definition.exists():
        ToolInstance.eject_standalone("boltz2", definition.parent)
    overrides = ("[set]\nDETECTED_COMPUTE_PLATFORM=cuda\nRECOMMENDED_TORCH_SPEC=torch==2.10.0\n"
                 "RECOMMENDED_TORCH_INDEX=https://download.pytorch.org/whl/cu128\n")
    target = definition / "env_vars.txt"
    if target.exists() and target.read_text() != overrides:
        raise SystemExit("Review existing Boltz-2 overrides before changing them.")
    target.write_text(overrides)
    os.environ["PROTO_BOLTZ2_STANDALONE_DIR"] = str(definition)
    instance = ToolInstance.get("boltz2")
    instance.ensure_ready()
    python = str(instance.env_path / "bin/python")
    freeze = subprocess.check_output([python, "-m", "pip", "freeze"], text=True)
    Path("data/corehpc/protease_design/boltz2_requirements_resolved.txt").write_text(freeze)
    subprocess.run([python, str(Path(__file__).with_name("stage_boltz2_weights.py"))], check=True)
    logging.info("Boltz-2 ready for offline validation: %s", instance.env_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
