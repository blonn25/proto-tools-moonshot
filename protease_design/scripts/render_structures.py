"""Prepare mapped native coordinates and render them with managed Open-Source PyMOL."""

import json
import os
import subprocess
from pathlib import Path

from Bio.SeqUtils import seq3

from analyze_structures import ca_positions, fit, read_reference


def write_native(path, atoms, sequence, rotation=None, translation=None):
    lines, chain, serial = [], None, 0
    for (position, name), coordinate in atoms.items():
        current = "A" if position <= 103 else "B"
        if chain is not None and chain != current:
            lines.append("TER")
        chain = current
        if rotation is not None:
            coordinate = coordinate @ rotation + translation
        serial += 1
        residue = seq3(sequence[position - 1]).upper()
        # Right-aligned one-letter element atom names follow PDB conventions.
        atom_name = f" {name:<3}" if len(name) < 4 else name
        x, y, z = coordinate
        lines.append(f"ATOM  {serial:5d} {atom_name} {residue:3} {chain}{position - 6:4d}    "
                     f"{x:8.3f}{y:8.3f}{z:8.3f}{1.0:6.2f}{0.0:6.2f}          {name[0]:>2}")
    path.write_text("\n".join(lines + ["TER", "END"]) + "\n")


def main():
    if not os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("Run rendering under the CPU SLURM template.")
    from proto_tools.utils import ToolInstance
    references = Path("data/corehpc/protease_design/references")
    output = Path("data/corehpc/protease_design/results/rendered")
    output.mkdir(parents=True, exist_ok=True)
    sequence = "FRLVTE" + json.loads((references / "P07339.json").read_text())["sequence"]["value"][64:]
    low = read_reference(references, "1LYA", "catd")
    high = read_reference(references, "1LYW", "catd")
    positions = sorted(set(ca_positions(low, "catd")) & set(ca_positions(high, "catd")))
    r, t, _ = fit([high[p, "CA"] for p in positions], [low[p, "CA"] for p in positions])
    write_native(output / "1LYA_mapped.pdb", low, sequence)
    write_native(output / "1LYW_aligned.pdb", high, sequence, r, t)
    python = ToolInstance.get("pymol_rmsd").env_path / "bin/python"
    if not python.is_file():
        raise SystemExit("Stage the managed PyMOL environment on the login node first.")
    subprocess.run([str(python), str(Path(__file__).with_name("render_pymol_worker.py")), str(output.resolve())], check=True)


if __name__ == "__main__":
    main()
