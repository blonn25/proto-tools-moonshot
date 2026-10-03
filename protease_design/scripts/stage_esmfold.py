"""Stage a managed GPU environment and pinned model snapshot on the login node."""

import argparse
import json
import logging
import os
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--torch-spec", required=True)
    parser.add_argument("--torch-index", required=True)
    args = parser.parse_args()
    if os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("Network staging belongs on the CoreHPC login node.")
    root = Path.cwd()
    if str(root) != "/mnt/scratch/group/CX500059_DS1/blonnquist/proto-tools-moonshot":
        raise SystemExit("Run from the documented CoreHPC mirror.")
    if not os.environ.get("PROTO_HOME", "").startswith(str(root) + "/"):
        raise SystemExit("Source corehpc_env.sh before staging.")
    from proto_tools.utils import ToolInstance

    destination = root / "data/corehpc/protease_design/env_defs/esmfold"
    if not destination.exists():
        ToolInstance.eject_standalone("esmfold", destination.parent)
    overrides = (
        "[set]\nDETECTED_COMPUTE_PLATFORM=cuda\n"
        f"RECOMMENDED_TORCH_SPEC={args.torch_spec}\n"
        f"RECOMMENDED_TORCH_INDEX={args.torch_index}\n"
    )
    definition = destination / "env_vars.txt"
    if definition.exists() and definition.read_text() != overrides:
        raise SystemExit("Existing environment overrides differ; review before rebuilding.")
    definition.write_text(overrides)
    os.environ["PROTO_ESMFOLD_STANDALONE_DIR"] = str(destination)
    instance = ToolInstance.get("esmfold")
    instance.ensure_ready()
    python = str(instance.env_path / "bin/python")
    freeze = subprocess.check_output([python, "-m", "pip", "freeze"], text=True)
    (root / "data/corehpc/protease_design/esmfold_requirements_resolved.txt").write_text(freeze)
    subprocess.run([python, str(Path(__file__).with_name("stage_esmfold_weights.py"))], check=True)
    logging.info("Managed ESMFold staging completed: %s", instance.env_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
