"""Sequence-derived assay metadata; not expression, solubility, or stability scores."""

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

import Bio
from Bio.SeqUtils import molecular_weight
from Bio.SeqUtils.ProtParam import ProteinAnalysis

from execution_provenance import revisions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, default=Path("data/corehpc/protease_design/results/assay_metadata"))
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("Use the CPU SLURM template.")
    records = [r for p in args.inputs for r in json.loads(p.read_text())["records"]]
    if len({r["id"] for r in records}) != len(records):
        raise ValueError("Duplicate sequence IDs.")
    rows = []
    for item in records:
        sequence = item["sequence"]
        if hashlib.sha256(sequence.encode()).hexdigest() != item["sequence_sha256"]:
            raise ValueError("Sequence checksum mismatch.")
        analysis = ProteinAnalysis(sequence)
        ss = 0 if item["id"] == "ADP_parent" else 4
        if sequence.count("C") != 2 * ss:
            raise ValueError("Unexpected cysteine count; review oxidation model.")
        reduced, oxidized = analysis.molar_extinction_coefficient()
        rows.append({"id": item["id"], "length": len(sequence),
            "average_mass_reduced_Da": analysis.molecular_weight(),
            "monoisotopic_mass_reduced_Da": molecular_weight(sequence, seq_type="protein", monoisotopic=True),
            "monoisotopic_mass_expected_disulfides_Da": molecular_weight(sequence, seq_type="protein", monoisotopic=True) - 2 * ss * 1.00782503223,
            "expected_disulfides": ss, "epsilon280_reduced_M_inverse_cm_inverse": reduced,
            "epsilon280_oxidized_M_inverse_cm_inverse": oxidized,
            "sequence_only_pI": analysis.isoelectric_point(), "GRAVY": analysis.gravy(),
            "sequence_sha256": item["sequence_sha256"]})
    args.output.mkdir(parents=True, exist_ok=True)
    result = {**revisions(), "job_id": os.environ["SLURM_JOB_ID"], "biopython": Bio.__version__,
              "note": "Untagged mature sequences; no glycans, salts, adducts, or processing heterogeneity. Predicted pI is not a solubility or pH-stability measurement.",
              "records": rows}
    (args.output / "assay_metadata.json").write_text(json.dumps(result, indent=2) + "\n")
    with (args.output / "assay_metadata.csv").open("w") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


if __name__ == "__main__":
    main()
