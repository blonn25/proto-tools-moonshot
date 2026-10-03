"""Build explicit enantiomeric substrate records and hydrolysis mass standards."""

import json
import os
from pathlib import Path

from rdkit import Chem, rdBase
from rdkit.Chem import Descriptors, rdMolDescriptors


def main():
    if not os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("Run under the CPU SLURM template.")
    output = Path("data/corehpc/protease_design/inputs/substrates")
    output.mkdir(parents=True, exist_ok=True)
    records = []
    for length in range(1, 5):
        parent = Chem.MolFromFASTA("F" * length)
        for label in ("L", "D"):
            molecule = Chem.Mol(parent)
            if label == "D":
                for atom in molecule.GetAtoms():
                    if atom.GetChiralTag() != Chem.ChiralType.CHI_UNSPECIFIED:
                        atom.InvertChirality()
            Chem.AssignStereochemistry(molecule, cleanIt=True, force=True)
            centers = Chem.FindMolChiralCenters(molecule, includeUnassigned=True)
            expected = "S" if label == "L" else "R"
            if len(centers) != length or any(cip != expected for _, cip in centers):
                raise RuntimeError("Phe substrate stereochemistry verification failed.")
            smiles = Chem.MolToSmiles(molecule, isomericSmiles=True)
            roundtrip = Chem.MolFromSmiles(smiles)
            if sorted(c for _, c in Chem.FindMolChiralCenters(roundtrip)) != [expected] * length:
                raise RuntimeError("Substrate stereochemistry lost during serialization.")
            name = f"{label}_Phe{length}_free_acid"
            mass = Descriptors.ExactMolWt(molecule)
            records.append({"id": name, "isomeric_smiles": smiles,
                            "formula": rdMolDescriptors.CalcMolFormula(molecule),
                            "neutral_monoisotopic_mass_Da": mass,
                            "mz_M_plus_H": mass + 1.007276466621,
                            "cip_centers": centers, "terminal_chemistry": "free amino / free carboxyl",
                            "role": "substrate" if length == 4 else "hydrolysis product standard"})
            writer = Chem.SDWriter(str(output / f"{name}.sdf"))
            molecule.SetProp("_Name", name)
            writer.write(molecule)
            writer.close()
    for length in range(1, 5):
        pair = [r for r in records if r["id"].split("_")[1] == f"Phe{length}"]
        if pair[0]["formula"] != pair[1]["formula"] or pair[0]["neutral_monoisotopic_mass_Da"] != pair[1]["neutral_monoisotopic_mass_Da"]:
            raise RuntimeError("Enantiomer mass mismatch.")
    # A single peptide-bond hydrolysis adds one water molecule, regardless of cut.
    masses = {n: records[(n - 1) * 2]["neutral_monoisotopic_mass_Da"] for n in range(1, 5)}
    water = Descriptors.ExactMolWt(Chem.MolFromSmiles("O"))
    for cut in (1, 2, 3):
        if abs(masses[cut] + masses[4 - cut] - masses[4] - water) > 1e-6:
            raise RuntimeError("Hydrolysis mass balance failed.")
    result = {"rdkit_version": rdBase.rdkitVersion, "job_id": os.environ["SLURM_JOB_ID"],
              "records": records,
              "note": "Chemical identity and theoretical masses only; no catalytic simulation or measurements."}
    (output / "substrates.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
