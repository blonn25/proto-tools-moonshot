"""Finite linker-torsion feasibility scan, not an equilibrium or pH ensemble.

Rotate two glycine phi bonds on a fixed 30-degree grid. Preserve all bond lengths,
angles, domain internal coordinates, and stereocenters. Reject new severe
cross-partition clashes and test both transferred native CatD conformations.
"""

import argparse
import hashlib
import json
import itertools
import math
import os
import shutil
from pathlib import Path

import numpy as np
from openmm import app
from scipy.spatial import cKDTree

from analyze_structures import ca_positions, fit, read_reference
from execution_provenance import revisions
from stereochemistry import audit, reference_signs


def rotate(coordinates, mask, origin, axis, degrees):
    result = coordinates.copy()
    vectors = coordinates[mask] - origin
    axis = axis / np.linalg.norm(axis)
    theta = math.radians(degrees)
    result[mask] = (vectors * math.cos(theta) + np.cross(axis, vectors) * math.sin(theta)
                   + np.outer(vectors @ axis, axis) * (1 - math.cos(theta)) + origin)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--predictions', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--include-first-psi', action='store_true')
    args = parser.parse_args()
    if not os.environ.get('SLURM_JOB_ID'):
        raise SystemExit('Use the CPU SLURM template.')
    reference_dir = Path('data/corehpc/protease_design/references')
    refs = {k: read_reference(reference_dir, k, d) for k, d in [('1LYA', 'catd'), ('1LYW', 'catd'), ('4Y7P', 'adp')]}
    signs = reference_signs(refs)
    for item in json.loads(args.input.read_text())['records']:
        source, output = args.predictions / item['id'], args.output / item['id']
        source_run = json.loads((source / 'run.json').read_text())
        lines = (source / 'structure.pdb').read_text().splitlines()
        if (source_run['sequence_sha256'] != item['sequence_sha256'] or
                source_run['structure_sha256'] != hashlib.sha256((source / 'structure.pdb').read_bytes()).hexdigest()):
            raise ValueError('Source provenance mismatch.')
        output.mkdir(parents=True, exist_ok=True)
        if item['kind'] != 'fusion':
            for name in ['structure.pdb', 'metrics.json', 'run.json']:
                shutil.copyfile(source / name, output / name)
            continue
        atom_lines = [i for i, line in enumerate(lines) if line.startswith('ATOM')]
        keys = [(int(lines[i][22:26]), lines[i][12:16].strip()) for i in atom_lines]
        key_index = {key: i for i, key in enumerate(keys)}
        coordinates = np.array([[float(lines[i][j:j+8]) for j in (30, 38, 46)] for i in atom_lines])
        heavy = np.array([not lines[i][76:78].strip().upper().startswith('H') for i in atom_lines])
        positions = np.array([key[0] for key in keys])
        cat_end = item['domains']['catd'][1]
        adp_start = item['domains']['adp'][0]
        spacer_start = cat_end + len('GGGGSLPETGGG') + 1
        middle = spacer_start + len(item['spacer_sequence']) // 2
        gly = [p for p in range(spacer_start, spacer_start + len(item['spacer_sequence'])) if item['sequence'][p-1] == 'G']
        pivots = [cat_end + 1, min(gly, key=lambda p: abs(p - middle))]
        if any(item['sequence'][p-1] != 'G' for p in pivots):
            raise ValueError('Phi pivots must be glycine.')
        joints = [(pivots[0], 'phi')]
        if args.include_first_psi:
            joints.append((pivots[0], 'psi'))
        joints.append((pivots[1], 'phi'))
        groups = np.zeros(len(keys), dtype=int)
        for group, (p, kind) in enumerate(joints, 1):
            same = np.array([name not in ('N', 'H', 'H1', 'H2', 'H3') if kind == 'phi'
                             else name in ('C', 'O', 'OXT') for _, name in keys])
            groups[(positions > p) | ((positions == p) & same)] = group
        # Exclude graph distances 1 and 2 from nonbonded clash checks.
        topology = app.PDBFile(str(source / 'structure.pdb')).topology
        neighbors = {i: set() for i in range(len(keys))}
        for a, b in topology.bonds():
            i = key_index[int(a.residue.id), a.name]
            j = key_index[int(b.residue.id), b.name]
            neighbors[i].add(j); neighbors[j].add(i)
        excluded = {i: {i} | neighbors[i] | set().union(*(neighbors[j] for j in neighbors[i])) for i in neighbors}
        heavy_indices = np.where(heavy)[0]
        cat_mask = heavy & (positions <= cat_end)
        adp_mask = heavy & (positions >= adp_start)
        other_cat = heavy & (positions > cat_end)
        other_adp = heavy & (positions < adp_start)
        transferred = {}
        for state in ['1LYA', '1LYW']:
            pp = ca_positions(refs[state], 'catd')
            rotation, translation, _ = fit([refs[state][p, 'CA'] for p in pp], [coordinates[key_index[p, 'CA']] for p in pp])
            transferred[state] = np.array(list(refs[state].values())) @ rotation + translation
        scans, best = [], None
        for angles in itertools.product(range(-180, 180, 30), repeat=len(joints)):
            xyz = coordinates.copy()
            for group, ((p, kind), angle) in enumerate(zip(joints, angles), 1):
                left, right = ('N', 'CA') if kind == 'phi' else ('CA', 'C')
                origin = xyz[key_index[p, left]]
                xyz = rotate(xyz, groups >= group, origin, xyz[key_index[p, right]] - origin, angle)
            pairs = cKDTree(xyz[heavy]).query_pairs(2.0, output_type='ndarray')
            clashes = 0
            for left, right in pairs:
                i, j = heavy_indices[left], heavy_indices[right]
                if groups[i] != groups[j] and j not in excluded[i]:
                    clashes += 1
            tree = cKDTree(xyz[adp_mask])
            state_min = {k: float(tree.query(v)[0].min()) for k, v in transferred.items()}
            raw_min = float(tree.query(xyz[cat_mask])[0].min())
            cat_pocket = float(cKDTree(xyz[other_cat]).query(xyz[[key_index[39, 'CG'], key_index[237, 'CG']]])[0].min())
            adp_pocket = float(cKDTree(xyz[other_adp]).query(xyz[key_index[adp_start + 78, 'OG']])[0])
            feasible = clashes == 0 and min(state_min.values()) >= 2.0 and raw_min >= 2.0 and min(cat_pocket, adp_pocket) >= 6.0
            entry = {'delta_torsion_degrees': list(angles), 'new_cross_partition_clash_pairs_below2A': clashes,
                     'transferred_state_minimum_A': state_min, 'interdomain_minimum_A': raw_min,
                     'partner_distance_to_catd_catalytic_atoms_A': cat_pocket,
                     'partner_distance_to_adp_serine_A': adp_pocket, 'geometrically_feasible': feasible}
            scans.append(entry)
            rank = (sum(abs(x) for x in angles), -min(state_min.values()))
            if feasible and (best is None or rank < best[0]):
                best = rank, xyz, entry
        result = {**revisions(), 'job_id': os.environ['SLURM_JOB_ID'], 'id': item['id'],
                  'source_structure_sha256': source_run['structure_sha256'], 'source_job_id': source_run['job_id'],
                  'pivot_phi_residues': pivots, 'torsion_joints': joints, 'grid_step_degrees': 30, 'tested': len(scans),
                  'feasible_grid_points': sum(row['geometrically_feasible'] for row in scans),
                  'note': 'Unweighted kinematic feasibility only. Not sampled thermodynamic populations, dynamics, or switching rates. Native-state transfer lacks unresolved/engineered residues.',
                  'grid': scans, 'selected': best[2] if best else None}
        (output / 'geometry_scan.json').write_text(json.dumps(result, indent=2) + '\n')
        if best is None:
            continue
        atoms = {key: best[1][i] for i, key in enumerate(keys) if heavy[i]}
        stereo = audit(atoms, item['sequence'], signs)
        if stereo['inverted_centers'] or stereo['degenerate_centers']:
            raise ValueError('Torsion rotation changed canonical stereochemistry.')
        for i, line_index in enumerate(atom_lines):
            x, y, z = best[1][i]
            lines[line_index] = lines[line_index][:30] + f'{x:8.3f}{y:8.3f}{z:8.3f}' + lines[line_index][54:]
        (output / 'structure.pdb').write_text('\n'.join(lines) + '\n')
        shutil.copyfile(source / 'metrics.json', output / 'metrics.json')
        record = {**source_run, **revisions(), 'job_id': os.environ['SLURM_JOB_ID'],
                  'kinematic_scan': {k: v for k, v in result.items() if k != 'grid'},
                  'confidence_note': 'Inherited predictor confidence; no recalculation for this constructed conformer.',
                  'structure_sha256': hashlib.sha256((output / 'structure.pdb').read_bytes()).hexdigest()}
        (output / 'run.json').write_text(json.dumps(record, indent=2) + '\n')


if __name__ == '__main__':
    main()
