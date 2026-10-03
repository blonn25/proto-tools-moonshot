"""Compare predicted domains to experimental structures without fitting away errors.

Requires the project Python dependencies (Biopython, numpy, scipy). Run under
the CPU SLURM template. No confidence score is interpreted as enzyme activity.
"""

import argparse
import csv
import hashlib
import json
import os
import subprocess
from pathlib import Path

import numpy as np
from Bio.PDB import PDBParser
from Bio.PDB.MMCIF2Dict import MMCIF2Dict
from Bio.SeqUtils import seq1
from scipy.spatial import cKDTree


def read_reference(directory, pdb_id, domain):
    """Index a chosen biological copy by construct position using SIFTS maps."""
    data = MMCIF2Dict(str(directory / f"{pdb_id}.cif"))
    entity_files = {"1": "entity"} if domain == "adp" else {"1": "entity", "2": "entity2"}
    maps = {}
    for entity, suffix in entity_files.items():
        record = json.loads((directory / f"{pdb_id}_{suffix}.json").read_text())
        alignment = record["rcsb_polymer_entity_align"]
        alignment = [a for a in alignment if a["reference_database_name"] == "UniProt"]
        if len(alignment) != 1:
            raise ValueError(f"Ambiguous mapping for {pdb_id} entity {entity}")
        mapping = {}
        for region in alignment[0]["aligned_regions"]:
            for i in range(region["length"]):
                precursor = region["ref_beg_seq_id"] + i
                mapping[region["entity_beg_seq_id"] + i] = precursor - (25 if domain == "adp" else 58)
        maps[entity] = mapping
    atoms = {}
    chains = {"A"} if domain == "adp" else {"A", "B"}
    columns = ["group_PDB", "label_asym_id", "label_entity_id", "label_seq_id",
               "label_atom_id", "label_alt_id", "type_symbol", "Cartn_x", "Cartn_y", "Cartn_z"]
    for row in zip(*(data[f"_atom_site.{key}"] for key in columns)):
        group, chain, entity, residue, atom, alt, element, x, y, z = row
        if group != "ATOM" or chain not in chains or alt not in (".", "A") or element == "H":
            continue
        position = maps[entity][int(residue)]
        atoms[position, atom] = np.array([float(x), float(y), float(z)])
    if not atoms:
        raise ValueError(f"No mapped atoms in {pdb_id}")
    return atoms


def fit(mobile, target):
    """Return a proper row-vector rigid transform, with no scaling/reflection."""
    mobile, target = np.asarray(mobile), np.asarray(target)
    mc, tc = mobile.mean(axis=0), target.mean(axis=0)
    u, _, vt = np.linalg.svd((mobile - mc).T @ (target - tc))
    correction = np.eye(3)
    correction[-1, -1] = np.linalg.det(u @ vt)
    rotation = u @ correction @ vt
    translation = tc - mc @ rotation
    deviations = np.linalg.norm(mobile @ rotation + translation - target, axis=1)
    return rotation, translation, deviations


def ca_positions(atoms, domain, framework=True):
    # CatD's native N-terminal 1-16 is the known mobile gate. Keep every other
    # resolved CA, including loops; do not choose the fitting mask from scores.
    return sorted(p for p, atom in atoms if atom == "CA" and
                  (not framework or domain != "catd" or p > 22))


def minimum_distance(a, b):
    if not a or not b:
        return None
    distances, _ = cKDTree(np.asarray(b)).query(np.asarray(a))
    return {"minimum_angstrom": float(distances.min()),
            "atoms_a_within_2A": int((distances < 2.0).sum()),
            "atoms_a_within_4A": int((distances < 4.0).sum())}


def read_prediction(path, sequence):
    structure = PDBParser(QUIET=True).get_structure("prediction", str(path))
    chains = list(structure[0])
    if len(chains) != 1:
        raise ValueError(f"Expected one continuous chain: {path}")
    residues = list(chains[0])
    if [r.id[1] for r in residues] != list(range(1, len(sequence) + 1)):
        raise ValueError(f"Non-contiguous prediction numbering: {path}")
    if "".join(seq1(r.resname) for r in residues) != sequence:
        raise ValueError(f"Prediction sequence mismatch: {path}")
    atoms, confidence = {}, {}
    raw = [float(r["CA"].bfactor) for r in residues]
    scale = 100.0 if max(raw) <= 1.05 else 1.0
    for residue in residues:
        confidence[residue.id[1]] = float(residue["CA"].bfactor) * scale
        for atom in residue:
            if atom.element != "H":
                atoms[residue.id[1], atom.name] = np.array(atom.coord, dtype=float)
    return atoms, confidence, scale


def domain_metrics(prediction, confidence, reference, domain, offset):
    positions = ca_positions(reference, domain)
    mobile = [prediction[p + offset, "CA"] for p in positions]
    target = [reference[p, "CA"] for p in positions]
    rotation, translation, deviations = fit(mobile, target)
    all_positions = ca_positions(reference, domain, framework=False)
    all_errors = [np.linalg.norm(prediction[p + offset, "CA"] @ rotation + translation - reference[p, "CA"])
                  for p in all_positions]
    motif = [(39, "CG"), (237, "CG")] if domain == "catd" else [
        (79, "OG"), (82, "NZ"), (176, "OH"), (317, "NE2")]
    predicted_motif = np.array([prediction[p + offset, atom] for p, atom in motif])
    native_motif = np.array([reference[p, atom] for p, atom in motif])
    errors = np.linalg.norm(predicted_motif @ rotation + translation - native_motif, axis=1)
    pair_errors = []
    for i in range(len(motif)):
        for j in range(i):
            pair_errors.append(abs(np.linalg.norm(predicted_motif[i] - predicted_motif[j]) -
                                   np.linalg.norm(native_motif[i] - native_motif[j])))
    scores = [confidence[p + offset] for p in all_positions]
    result = {
        "framework_n_ca": len(positions), "resolved_n_ca": len(all_positions),
        "framework_rmsd_A": float(np.sqrt(np.mean(deviations ** 2))),
        "all_resolved_rmsd_on_framework_fit_A": float(np.sqrt(np.mean(np.square(all_errors)))),
        "resolved_mean_plddt": float(np.mean(scores)),
        "resolved_fraction_plddt_below70": float(np.mean(np.array(scores) < 70)),
        "catalytic_sidechain_rmsd_on_framework_fit_A": float(np.sqrt(np.mean(errors ** 2))),
        "catalytic_pair_distance_max_error_A": float(max(pair_errors)),
        "catalytic_atoms": [f"{p + offset}:{atom}" for p, atom in motif],
    }
    if domain == "catd":
        result["disulfide_distances_A"] = [float(np.linalg.norm(
            prediction[p + offset, "SG"] - prediction[q + offset, "SG"]))
            for p, q in ((33, 102), (52, 59), (228, 232), (271, 308))]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--references", type=Path, default=Path("data/corehpc/protease_design/references"))
    parser.add_argument("--inputs", type=Path, default=Path("data/corehpc/protease_design/inputs"))
    parser.add_argument("--predictions", type=Path, default=Path("data/corehpc/protease_design/results/esmfold"))
    parser.add_argument("--output", type=Path, default=Path("data/corehpc/protease_design/results/analysis"))
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("Run scientific analysis under the CPU SLURM template.")
    references = {key: read_reference(args.references, key, domain)
                  for key, domain in (("4Y7P", "adp"), ("1LYA", "catd"), ("1LYW", "catd"))}
    positions = sorted(set(ca_positions(references["1LYA"], "catd")) &
                       set(ca_positions(references["1LYW"], "catd")))
    rotation, translation, deviations = fit(
        [references["1LYW"][p, "CA"] for p in positions],
        [references["1LYA"][p, "CA"] for p in positions])
    native_comparison = {
        "framework_rmsd_A": float(np.sqrt(np.mean(deviations ** 2))),
        "native_gate_residue_CA_displacements_A": {
            str(p - 6): float(np.linalg.norm(references["1LYW"][p, "CA"] @ rotation + translation -
                                            references["1LYA"][p, "CA"]))
            for p in range(7, 23) if (p, "CA") in references["1LYA"] and (p, "CA") in references["1LYW"]},
    }
    records = []
    for filename in ("controls.json", "candidates.json"):
        records.extend(json.loads((args.inputs / filename).read_text())["records"])
    results, missing = [], []
    for item in records:
        directory = args.predictions / item["id"]
        if not (directory / "run.json").exists():
            missing.append(item["id"])
            continue
        run = json.loads((directory / "run.json").read_text())
        if run["sequence_sha256"] != item["sequence_sha256"]:
            raise ValueError(f"Input hash mismatch: {item['id']}")
        pdb = directory / "structure.pdb"
        if hashlib.sha256(pdb.read_bytes()).hexdigest() != run["structure_sha256"]:
            raise ValueError(f"Structure hash mismatch: {pdb}")
        atoms, confidence, scale = read_prediction(pdb, item["sequence"])
        prediction_metrics = json.loads((directory / "metrics.json").read_text())
        domains = item.get("domains", {"adp" if item["id"] == "ADP_parent" else "catd": [1, item["length"]]})
        row = {"id": item["id"], "kind": item["kind"], "length": item["length"],
               "pdb_confidence_multiplier": scale, "prediction_job": run["job_id"],
               "sequence_sha256": item["sequence_sha256"], "domains": {}}
        # Same ordered atom convention for every non-glycine L residue,
        # including cysteine (whose CIP label differs from most L residues).
        reference_volumes = []
        for native in references.values():
            for p in ca_positions(native, "adp", framework=False):
                if all((p, a) in native for a in ("N", "C", "CA", "CB")):
                    reference_volumes.append(float(np.dot(native[p, "N"] - native[p, "CA"],
                        np.cross(native[p, "C"] - native[p, "CA"], native[p, "CB"] - native[p, "CA"]))))
        expected_sign = np.sign(np.median(reference_volumes))
        incorrect_chirality, degenerate_chirality = [], []
        for p, residue in enumerate(item["sequence"], 1):
            if residue == "G":
                continue
            volume = float(np.dot(atoms[p, "N"] - atoms[p, "CA"],
                                  np.cross(atoms[p, "C"] - atoms[p, "CA"], atoms[p, "CB"] - atoms[p, "CA"])))
            if abs(volume) < 0.1:
                degenerate_chirality.append(p)
            elif np.sign(volume) != expected_sign:
                incorrect_chirality.append(p)
        row["alpha_chirality_inverted_positions"] = incorrect_chirality
        row["alpha_chirality_degenerate_positions"] = degenerate_chirality
        row["global_ptm"] = prediction_metrics.get("ptm")
        for domain in ("catd", "adp"):
            if domain not in domains:
                continue
            start, end = domains[domain]
            native_id = "1LYA" if domain == "catd" else "4Y7P"
            row["domains"][domain] = domain_metrics(atoms, confidence, references[native_id], domain, start - 1)
            row["domains"][domain]["full_domain_mean_plddt"] = float(np.mean([confidence[p] for p in range(start, end + 1)]))
        if item["kind"] == "fusion":
            adp_start = domains["adp"][0]
            cat_atoms = [v for (p, a), v in atoms.items() if p <= domains["catd"][1]]
            adp_atoms = [v for (p, a), v in atoms.items() if p >= adp_start]
            row["interdomain_contacts"] = minimum_distance(cat_atoms, adp_atoms)
            cat_keys = [key for key in atoms if key[0] <= domains["catd"][1]]
            adp_keys = [key for key in atoms if key[0] >= adp_start]
            tree = cKDTree([atoms[key] for key in adp_keys])
            clashes = []
            for key in cat_keys:
                for index in tree.query_ball_point(atoms[key], 2.0):
                    partner = adp_keys[index]
                    clashes.append({"catd_position": key[0], "catd_atom": key[1],
                                    "adp_position": partner[0], "adp_atom": partner[1],
                                    "distance_A": float(np.linalg.norm(atoms[key] - atoms[partner])),
                                    "catd_plddt": confidence[key[0]], "adp_plddt": confidence[partner[0]]})
            row["interdomain_clash_pairs_below2A"] = sorted(clashes, key=lambda c: c["distance_A"])
            cat_resolved = set(ca_positions(references["1LYA"], "catd", framework=False))
            adp_resolved = {p + adp_start - 1 for p in ca_positions(references["4Y7P"], "adp")}
            row["resolved_interdomain_contacts"] = minimum_distance(
                [atoms[key] for key in cat_keys if key[0] in cat_resolved],
                [atoms[key] for key in adp_keys if key[0] in adp_resolved])
            if prediction_metrics.get("pae") is not None:
                pae = np.asarray(prediction_metrics["pae"])
                if pae.shape != (item["length"], item["length"]):
                    raise ValueError(f"Unexpected PAE shape for {item['id']}: {pae.shape}")
                ii = np.array(sorted(cat_resolved)) - 1
                jj = np.array(sorted(adp_resolved)) - 1
                row["resolved_PAE_A"] = {
                    "catd_within": float(pae[np.ix_(ii, ii)].mean()),
                    "adp_within": float(pae[np.ix_(jj, jj)].mean()),
                    "interdomain_bidirectional": float(0.5 * (pae[np.ix_(ii, jj)].mean() + pae[np.ix_(jj, ii)].mean()))}
            row["partner_distance_to_catalytic_atoms"] = {
                "catd": minimum_distance([atoms[p, "CG"] for p in (39, 237)], adp_atoms),
                "adp": minimum_distance([atoms[adp_start + 78, "OG"]], cat_atoms),
            }
            row["transferred_catd_states"] = {}
            for state in ("1LYA", "1LYW"):
                native = references[state]
                pp = ca_positions(native, "catd")
                r, t, _ = fit([native[p, "CA"] for p in pp], [atoms[p, "CA"] for p in pp])
                transferred = [v @ r + t for v in native.values()]
                row["transferred_catd_states"][state] = minimum_distance(transferred, adp_atoms)
            row["linker_mean_plddt"] = float(np.mean([confidence[p] for p in range(*[domains["linker"][0], domains["linker"][1] + 1])]))
        results.append(row)
    controls = {r["id"]: r for r in results if r["kind"] == "isolated_domain"}
    for row in results:
        if row["kind"] != "fusion":
            continue
        variant = row["id"].split("_")[1]
        for domain, parent in (("catd", f"srCatD_{variant}"), ("adp", "ADP_parent")):
            if parent in controls:
                score = row["domains"][domain]
                control = controls[parent]["domains"][domain]
                score["framework_rmsd_delta_from_parent_A"] = score["framework_rmsd_A"] - control["framework_rmsd_A"]
                score["plddt_delta_from_parent"] = score["resolved_mean_plddt"] - control["resolved_mean_plddt"]
    args.output.mkdir(parents=True, exist_ok=True)
    output = {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
              "job_id": os.environ["SLURM_JOB_ID"], "native_catd_state_comparison": native_comparison,
              "records": results, "missing_predictions": missing}
    (args.output / "structural_analysis.json").write_text(json.dumps(output, indent=2) + "\n")
    with (args.output / "domain_metrics.csv").open("w") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "domain", "resolved_mean_plddt", "framework_rmsd_A", "catalytic_sidechain_rmsd_A"])
        for row in results:
            for domain, score in row["domains"].items():
                writer.writerow([row["id"], domain, score["resolved_mean_plddt"], score["framework_rmsd_A"],
                                 score["catalytic_sidechain_rmsd_on_framework_fit_A"]])


if __name__ == "__main__":
    main()
