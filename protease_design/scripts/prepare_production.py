"""Specify expression intermediates and verify the final sortase product sequence.

These are proposed constructs, not recovered plasmid sequences or proven yields.
The published CatD maturation junction is mapped onto the UniProt proenzyme.
"""

import argparse
import hashlib
import json
from pathlib import Path

from generate_candidates import CANONICAL, record


def production_records(candidates, precursor):
    native_region = "IAKGPVSKYSQAVPAVTEGPIPE"
    engineered_region = "IAKGPVSKPIEFFRLVTEGPIPE"
    if precursor.count(native_region) != 1:
        raise ValueError("Published maturation-region mapping failed.")
    engineered = precursor.replace(native_region, engineered_region)
    # Signal peptide 1–20 is omitted for cytoplasmic bacterial expression.
    # Native mature CatD begins at precursor 65. The engineered cleavage is F|F.
    prelude = engineered[20:58]
    if prelude[-5:] != "KPIEF" or engineered[58:64] != "FRLVTE":
        raise ValueError("Engineered activation boundary does not yield FRLVTE.")
    donors, acceptors, assemblies = {}, {}, []
    for candidate in candidates:
        sequence = candidate["sequence"]
        catd_end = candidate["domains"]["catd"][1]
        adp_start = candidate["domains"]["adp"][0]
        catd = sequence[:catd_end]
        adp = sequence[adp_start - 1:]
        variant, spacer = candidate["catd_variant"], candidate["spacer_name"]
        donor = "M" + prelude + catd + "GGGGSLPETGGHHHHHH"
        acceptor_processed = "GGG" + candidate["spacer_sequence"] + "GGS" + adp
        acceptor = "MHHHHHHGSSENLYFQ" + acceptor_processed
        # CatD prosequence is removed first; sortase removes G-G-His6 from donor.
        matured_donor = donor[1 + len(prelude):]
        retained_donor, released_tail = matured_donor.rsplit("LPET", 1)
        if released_tail != "GGHHHHHH":
            raise ValueError("Unexpected sortase donor tail.")
        product = retained_donor + "LPET" + acceptor_processed
        if product != sequence or set(donor + acceptor) - CANONICAL:
            raise ValueError("Assembly does not reproduce the canonical mature design.")
        donor_id, acceptor_id = f"donor_{variant}", f"acceptor_{spacer}"
        donors[donor_id] = record(donor_id, donor, kind="proposed_expression_intermediate",
            mature_donor_sequence=matured_donor, removed_activation_prefix=donor[:1 + len(prelude)],
            activation_junction="KPIEF|FRLVTE", source="P07339:21-412 with Beyer1996 Table I junction")
        acceptors[acceptor_id] = record(acceptor_id, acceptor, kind="proposed_expression_intermediate",
            processed_acceptor_sequence=acceptor_processed, tag_removal_junction="ENLYFQ|GGG",
            source="P94288:26-388 with proposed N-terminal His6/TEV tag and spacer")
        assemblies.append({"id": candidate["id"], "donor": donor_id, "acceptor": acceptor_id,
                           "product_sequence_sha256": hashlib.sha256(product.encode()).hexdigest(),
                           "sequence_verified_assembly": True})
    return {"donors": list(donors.values()), "acceptors": list(acceptors.values()), "assemblies": assemblies}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=Path("data/corehpc/protease_design/inputs/candidates.json"))
    parser.add_argument("--references", type=Path, default=Path("data/corehpc/protease_design/references"))
    parser.add_argument("--output", type=Path, default=Path("data/corehpc/protease_design/inputs/production"))
    args = parser.parse_args()
    precursor = json.loads((args.references / "P07339.json").read_text())["sequence"]["value"]
    result = production_records(json.loads(args.candidates.read_text())["records"], precursor)
    result["evidence"] = {"junction_doi": "10.1074/jbc.271.26.15590", "location": "Table I, p. 15592",
        "status": "Sequence-defined proposal. Vector context and tags are new; no expression/ligation validation.",
        "source_url": "https://doi.org/10.1074/jbc.271.26.15590"}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "production.json").write_text(json.dumps(result, indent=2) + "\n")
    for key in ("donors", "acceptors"):
        (args.output / f"{key}.fasta").write_text("".join(f">{r['id']}\n{r['sequence']}\n" for r in result[key]))


if __name__ == "__main__":
    main()
