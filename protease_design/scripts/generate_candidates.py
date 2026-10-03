"""Generate the prospective 24-member fusion library with explicit residue maps."""

import argparse
import hashlib
import json
import logging
from pathlib import Path

CANONICAL = set("ACDEFGHIKLMNPQRSTVWY")
VARIANTS = {"WT": None, "E180Q": (180, "E", "Q"), "D187N": (187, "D", "N"), "Y10F": (10, "Y", "F")}


def record(name, sequence, **metadata):
    if set(sequence) - CANONICAL:
        raise ValueError(f"Noncanonical residue in {name}")
    return {"id": name, "sequence": sequence, "length": len(sequence),
            "sequence_sha256": hashlib.sha256(sequence.encode()).hexdigest(), **metadata}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--references", type=Path, default=Path("data/corehpc/protease_design/references"))
    parser.add_argument("--output", type=Path, default=Path("data/corehpc/protease_design/inputs"))
    parser.add_argument("--flexible-repeats", type=int, nargs="+", default=[1, 3, 5])
    parser.add_argument("--helical-repeats", type=int, nargs="*", default=[2, 4, 6])
    args = parser.parse_args()
    if any(n < 1 for n in args.flexible_repeats + args.helical_repeats):
        raise SystemExit("Spacer repeat counts must be positive.")
    sequences = {}
    sources = {}
    for accession in ("P07339", "P94288"):
        path = args.references / f"{accession}.json"
        data = path.read_bytes()
        sequences[accession] = json.loads(data)["sequence"]["value"]
        sources[accession] = {"file": str(path), "sha256": hashlib.sha256(data).hexdigest()}
    if len(sequences["P07339"]) != 412 or len(sequences["P94288"]) != 388:
        raise ValueError("Reference lengths changed; review annotation before regenerating.")
    catd = sequences["P07339"][64:]
    adp = sequences["P94288"][25:]
    for position, residue in ((104, "S"), (107, "K"), (201, "Y"), (342, "H")):
        if sequences["P94288"][position - 1] != residue:
            raise ValueError(f"ADP catalytic mapping mismatch at precursor {position}")
    spacers = {f"GS{n}": "GGGGS" * n for n in args.flexible_repeats}
    spacers.update({f"H{n}": "EAAAK" * n for n in args.helical_repeats})
    fusions = []
    controls = [record("ADP_parent", adp, kind="isolated_domain", source="P94288:26-388")]
    for variant, substitution in VARIANTS.items():
        domain = catd
        if substitution:
            position, original, replacement = substitution
            if domain[position - 1] != original:
                raise ValueError(f"Cathepsin-D numbering mismatch for {variant}")
            domain = domain[:position - 1] + replacement + domain[position:]
        domain = "FRLVTE" + domain
        controls.append(record(f"srCatD_{variant}", domain, kind="isolated_domain", catd_variant=variant))
        for spacer_name, spacer in spacers.items():
            linker = "GGGGS" + "LPETGGG" + spacer + "GGS"
            adp_start = len(domain) + len(linker) + 1
            fusions.append(record(
                f"CDAD_{variant}_{spacer_name}", domain + linker + adp,
                kind="fusion", catd_variant=variant, spacer_name=spacer_name,
                spacer_sequence=spacer, linker_sequence=linker,
                domains={"catd": [1, len(domain)], "linker": [len(domain) + 1, adp_start - 1],
                         "adp": [adp_start, adp_start + len(adp) - 1]},
                catd_native_to_fusion_offset=6,
                adp_precursor_to_fusion_offset=adp_start - 26,
                adp_pdb_author_to_fusion_offset=adp_start + 4,
                catalytic_positions={"catd": [39, 237],
                    "adp": [adp_start + p - 26 for p in (104, 107, 201, 342)]},
                catd_disulfides=[[p - 58, q - 58] for p, q in ((91, 160), (110, 117), (286, 290), (329, 366))],
            ))
    args.output.mkdir(parents=True, exist_ok=True)
    for name, items in (("candidates", fusions), ("controls", controls)):
        (args.output / f"{name}.json").write_text(json.dumps({"sources": sources, "records": items}, indent=2) + "\n")
        (args.output / f"{name}.fasta").write_text("".join(f">{r['id']}\n{r['sequence']}\n" for r in items))
    logging.info("Generated %d candidate sequences and %d isolated-domain controls", len(fusions), len(controls))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
