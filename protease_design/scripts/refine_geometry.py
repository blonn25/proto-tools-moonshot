"""Restrained CPU geometry repair; not dynamics, a pH model, or activity evidence."""

import argparse
import faulthandler
import hashlib
import io
import json
import logging
import os
import random
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import openmm as mm
from openmm import app, unit

from execution_provenance import revisions


def use_builtin_obc2(system, positions, platform, threads):
    """Use OpenMM's optimized OBC2 kernel after checking solvent-energy equivalence.

The XML constructs a generic CustomGBForce. Its offset radius is r-0.009 nm
and its third parameter is scale*(r-0.009). The built-in kernel takes r and
scale directly. Preserve charges, dielectrics, ACE surface energy, and no cutoff.
"""
    custom = [(i, f) for i, f in enumerate(system.getForces()) if isinstance(f, mm.CustomGBForce)]
    if len(custom) != 1:
        raise ValueError("Expected one OBC2 CustomGBForce.")
    index, original = custom[0]
    names = [original.getPerParticleParameterName(i) for i in range(original.getNumPerParticleParameters())]
    if names != ["charge", "or", "sr"] or original.getNonbondedMethod() != mm.CustomGBForce.NoCutoff:
        raise ValueError("Unexpected OBC2 parameterization.")
    replacement = mm.GBSAOBCForce()
    replacement.setSoluteDielectric(1.0)
    replacement.setSolventDielectric(78.5)
    replacement.setSurfaceAreaEnergy(2.25936 * unit.kilojoule_per_mole / unit.nanometer**2)
    replacement.setNonbondedMethod(mm.GBSAOBCForce.NoCutoff)
    for i in range(original.getNumParticles()):
        charge, offset_radius, scaled_radius = original.getParticleParameters(i)
        replacement.addParticle(charge, offset_radius + 0.009, scaled_radius / offset_radius)
    original.setForceGroup(1)
    replacement.setForceGroup(1)
    frames = [np.array(positions.value_in_unit(unit.nanometer))]
    for atom, axis, delta in [(0, 0, 0.002), (system.getNumParticles() // 2, 1, -0.003)]:
        frame = frames[0].copy()
        frame[atom, axis] += delta
        frames.append(frame)

    def energies():
        integrator = mm.VerletIntegrator(0.001 * unit.picosecond)
        context = mm.Context(system, integrator, platform, {"Threads": str(threads)})
        values = []
        for frame in frames:
            context.setPositions(frame * unit.nanometer)
            values.append(context.getState(getEnergy=True, groups=2).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole))
        del context, integrator
        return values

    before = energies()
    system.removeForce(index)
    system.addForce(replacement)
    after = energies()
    errors = [abs(a - b) for a, b in zip(before, after)]
    if not np.isfinite(before + after).all() or any(
            e > max(0.1, abs(a) * 1e-6) for e, a in zip(errors, before)):
        raise ValueError(f"Optimized OBC2 failed solvent-energy equivalence: {before}, {after}")
    return {"custom_solvent_energies_kJ_mol": before, "builtin_solvent_energies_kJ_mol": after,
            "absolute_errors_kJ_mol": errors,
            "tolerance": "max(0.1 kJ/mol, 1e-6 * abs(custom solvent energy)) per frame",
            "frames": "Original and two local coordinate perturbations; no minimization before comparison."}


def prepare_topology(pdb, disulfides):
    """Preserve intended disulfides and supply the missing terminal OXT if needed."""
    residues = list(pdb.topology.residues())
    atom_map = {(int(a.residue.id), a.name): a for a in pdb.topology.atoms()}
    expected = {frozenset(pair) for pair in disulfides}
    existing = set()
    for a, b in pdb.topology.bonds():
        if a.name == b.name == "SG":
            pair = frozenset((int(a.residue.id), int(b.residue.id)))
            if pair not in expected:
                raise ValueError(f"Unexpected predicted disulfide: {pair}")
            existing.add(pair)
    for p, q in disulfides:
        if frozenset((p, q)) not in existing:
            pdb.topology.addBond(atom_map[p, "SG"], atom_map[q, "SG"])
    last = residues[-1]
    atoms = {a.name: a for a in last.atoms()}
    positions = np.array(pdb.positions.value_in_unit(unit.nanometer))
    if "OXT" not in atoms:
        c, ca, oxygen = [positions[atoms[name].index] for name in ("C", "CA", "O")]
        axis = (c - ca) / np.linalg.norm(c - ca)
        vector = oxygen - c
        oxt = c + 2 * vector.dot(axis) * axis - vector
        atom = pdb.topology.addAtom("OXT", app.element.oxygen, last)
        pdb.topology.addBond(atoms["C"], atom)
        positions = np.vstack((positions, oxt))
    return app.Modeller(pdb.topology, positions * unit.nanometer)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--shard", type=int, default=0)
    parser.add_argument("--shards", type=int, default=1)
    parser.add_argument("--predictions", type=Path, default=Path("data/corehpc/protease_design/results/esmfold"))
    parser.add_argument("--output", type=Path, default=Path("data/corehpc/protease_design/results/esmfold_refined"))
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--threads", type=int)
    args = parser.parse_args()
    if not os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("Use the CPU SLURM template.")
    if args.shards < 1 or not 0 <= args.shard < args.shards:
        raise SystemExit("Invalid shard selection.")
    threads = args.threads or int(os.environ["SLURM_CPUS_PER_TASK"])
    if threads < 1 or threads > int(os.environ["SLURM_CPUS_PER_TASK"]):
        raise SystemExit("Threads must fit the CPU allocation.")
    os.environ["OPENMM_CPU_THREADS"] = str(threads)
    faulthandler.enable()
    faulthandler.dump_traceback_later(300, repeat=True)
    records = json.loads(args.input.read_text())["records"]
    if args.only:
        if set(args.only) - {r["id"] for r in records}:
            raise SystemExit("Unknown sequence ID.")
        records = [r for r in records if r["id"] in args.only]
    records = records[args.shard::args.shards]
    platform = mm.Platform.getPlatformByName("CPU")
    platform.setPropertyDefaultValue("Threads", str(threads))
    for item in records:
        start = time.monotonic()
        random.seed(20261002)
        np.random.seed(20261002)
        source = args.predictions / item["id"]
        prior = json.loads((source / "run.json").read_text())
        source_hash = hashlib.sha256((source / "structure.pdb").read_bytes()).hexdigest()
        if source_hash != prior["structure_sha256"] or prior["sequence_sha256"] != item["sequence_sha256"]:
            raise ValueError("Prediction provenance mismatch.")
        output = args.output / item["id"]
        output.mkdir(parents=True, exist_ok=True)
        if (output / "run.json").exists():
            old = json.loads((output / "run.json").read_text())
            if (old["refinement"]["source_structure_sha256"] != source_hash or
                    old["refinement"]["max_iterations"] != args.iterations):
                raise ValueError("Existing refinement differs from input/configuration.")
            continue
        pdb = app.PDBFile(str(source / "structure.pdb"))
        ss = item.get("catd_disulfides", [] if item["id"] == "ADP_parent" else
                      [[33, 102], [52, 59], [228, 232], [271, 308]])
        modeller = prepare_topology(pdb, ss)
        logging.info("%s: adding hydrogens with %d CPU threads", item["id"], threads)
        forcefield = app.ForceField("amber14/protein.ff14SB.xml", "implicit/obc2.xml")
        # Fixed standard protonation is a geometry-preparation convention only.
        modeller.addHydrogens(forcefield, pH=7.0, platform=platform)
        logging.info("%s: hydrogens ready at %.1f s; creating restrained system", item["id"], time.monotonic() - start)
        system = forcefield.createSystem(modeller.topology, nonbondedMethod=app.NoCutoff,
                                         constraints=app.HBonds)
        equivalence = use_builtin_obc2(system, modeller.positions, platform, threads)
        logging.info("%s: optimized OBC2 equivalence errors %s kJ/mol", item["id"], equivalence["absolute_errors_kJ_mol"])
        restraint = mm.CustomExternalForce("0.5*k*((x-x0)^2+(y-y0)^2+(z-z0)^2)")
        restraint.addGlobalParameter("k", 1000.0)
        for name in ("x0", "y0", "z0"):
            restraint.addPerParticleParameter(name)
        initial = np.array(modeller.positions.value_in_unit(unit.nanometer))
        ca_indices = []
        for atom in modeller.topology.atoms():
            if atom.name == "CA":
                restraint.addParticle(atom.index, initial[atom.index].tolist())
                ca_indices.append(atom.index)
        system.addForce(restraint)
        integrator = mm.VerletIntegrator(0.001 * unit.picosecond)
        context = mm.Context(system, integrator, platform, {"Threads": str(threads)})
        context.setPositions(modeller.positions)
        before = context.getState(getEnergy=True).getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
        logging.info("%s: initial energy %.3f kJ/mol at %.1f s; minimizing", item["id"], before, time.monotonic() - start)
        mm.LocalEnergyMinimizer.minimize(context, 10 * unit.kilojoule_per_mole / unit.nanometer,
                                        args.iterations)
        state = context.getState(getPositions=True, getEnergy=True, getForces=True)
        final = np.array(state.getPositions().value_in_unit(unit.nanometer))
        after = state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
        forces = np.array(state.getForces().value_in_unit(unit.kilojoule_per_mole / unit.nanometer))
        if not np.isfinite(final).all() or not np.isfinite(after) or after > before:
            raise RuntimeError("Refinement failed finite-coordinate or energy-descent checks.")
        text = io.StringIO()
        app.PDBFile.writeFile(modeller.topology, state.getPositions(), text, keepIds=True)
        confidence = {}
        for line in (source / "structure.pdb").read_text().splitlines():
            if line.startswith("ATOM"):
                confidence[int(line[22:26]), line[12:16].strip()] = line[60:66]
        lines = []
        for line in text.getvalue().splitlines():
            if line.startswith("ATOM"):
                key = (int(line[22:26]), line[12:16].strip())
                line = line[:60] + confidence.get(key, "  0.00") + line[66:]
            lines.append(line)
        (output / "structure.pdb").write_text("\n".join(lines) + "\n")
        (output / "metrics.json").write_text((source / "metrics.json").read_text())
        refinement = {
            "method": "restrained geometry minimization; no MD steps", "openmm": mm.__version__,
            "platform": "CPU", "threads": threads,
            "forcefield": ["amber14/protein.ff14SB.xml", "implicit/obc2.xml"],
            "solvent_implementation": "GBSAOBCForce optimized CPU kernel, mapped from XML CustomGBForce",
            "solvent_energy_equivalence": equivalence,
            "standard_protonation_pH": 7.0, "restraint_CA_k_kJ_mol_nm2": 1000,
            "max_iterations": args.iterations, "force_tolerance_kJ_mol_nm": 10,
            "energy_before_kJ_mol": before, "energy_after_kJ_mol": after,
            "final_force_rms_kJ_mol_nm": float(np.sqrt(np.mean(forces ** 2))),
            "CA_rms_displacement_A": float(10 * np.sqrt(np.mean(np.sum((final[ca_indices] - initial[ca_indices]) ** 2, axis=1)))),
            "source_structure_sha256": source_hash, "source_job_id": prior["job_id"],
            "source_commit": prior["commit"],
            "confidence_note": "pLDDT/PAE copied from original prediction; not re-estimated after refinement.",
        }
        result = {**prior, **revisions(),
                  "job_id": os.environ["SLURM_JOB_ID"], "refinement": refinement,
                  "completed_utc": datetime.now(timezone.utc).isoformat(),
                  "elapsed_seconds": time.monotonic() - start,
                  "structure_sha256": hashlib.sha256((output / "structure.pdb").read_bytes()).hexdigest()}
        temporary = output / "run.json.part"
        temporary.write_text(json.dumps(result, indent=2) + "\n")
        temporary.replace(output / "run.json")
        logging.info("Refined %s in %.1f seconds; CA shift %.3f A", item["id"], result["elapsed_seconds"],
                     refinement["CA_rms_displacement_A"])
        del context, integrator


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
