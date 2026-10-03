"""Independent coordinate audit of selected torsion-scan conformers."""

import argparse
import hashlib
import itertools
import json
import math
import os
from pathlib import Path

import numpy as np
from openmm import app, unit

from analyze_structures import fit, read_reference
from execution_provenance import revisions
from stereochemistry import audit, reference_signs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--scans', type=Path, required=True)
    args = parser.parse_args()
    if not os.environ.get('SLURM_JOB_ID'):
        raise SystemExit('Use the CPU SLURM template.')
    refdir = Path('data/corehpc/protease_design/references')
    signs = reference_signs({k: read_reference(refdir, k, d) for k, d in [('1LYA','catd'),('4Y7P','adp')]})
    results = []
    for record in json.loads(args.input.read_text())['records']:
        if record['kind'] != 'fusion':
            continue
        directory = args.scans / record['id']
        scan = json.loads((directory / 'geometry_scan.json').read_text())
        if not scan['selected']:
            results.append({'id': record['id'], 'status': 'No feasible grid point'})
            continue
        source_path = args.source / record['id'] / 'structure.pdb'
        if hashlib.sha256(source_path.read_bytes()).hexdigest() != scan['source_structure_sha256']:
            raise ValueError('Scan source hash mismatch.')
        source, target = [app.PDBFile(str(p)) for p in [source_path, directory / 'structure.pdb']]
        a, b = [np.array(p.positions.value_in_unit(unit.angstrom)) for p in [source, target]]
        atoms = list(source.topology.atoms())
        keys = [(int(x.residue.id), x.name) for x in atoms]
        if keys != [(int(x.residue.id), x.name) for x in target.topology.atoms()]:
            raise ValueError('Atom identity/order changed.')
        bonds = [(left.index, right.index) for left, right in source.topology.bonds()]
        bond_error = max(abs(np.linalg.norm(a[i]-a[j])-np.linalg.norm(b[i]-b[j])) for i,j in bonds)
        neighbors = {i:set() for i in range(len(atoms))}
        for i,j in bonds:
            neighbors[i].add(j);neighbors[j].add(i)
        angle_error = 0
        for center, connected in neighbors.items():
            for i,j in itertools.combinations(connected,2):
                angles=[]
                for xyz in [a,b]:
                    v,w=xyz[i]-xyz[center],xyz[j]-xyz[center]
                    angles.append(math.degrees(math.acos(np.clip(np.dot(v,w)/np.linalg.norm(v)/np.linalg.norm(w),-1,1))))
                angle_error=max(angle_error,abs(angles[0]-angles[1]))
        domains={}
        for name in ['catd','adp']:
            start,end=record['domains'][name]
            indices=[i for i,x in enumerate(atoms) if start<=int(x.residue.id)<=end and x.element.symbol!='H']
            _,_,deviations=fit(a[indices],b[indices])
            domains[name]=float(np.sqrt(np.mean(deviations**2)))
        stereo=audit({key:b[i] for i,key in enumerate(keys) if atoms[i].element.symbol!='H'},record['sequence'],signs)
        if bond_error>0.005 or angle_error>0.5 or max(domains.values())>0.005 or stereo['inverted_centers'] or stereo['degenerate_centers']:
            raise ValueError(f'Kinematic invariance failed for {record["id"]}.')
        results.append({'id':record['id'],'status':'passed','maximum_bond_length_change_A':float(bond_error),
                        'maximum_bond_angle_change_degrees':float(angle_error),'domain_heavy_atom_rigid_fit_RMSD_A':domains,
                        'canonical_stereochemistry':stereo,'structure_sha256':hashlib.sha256((directory/'structure.pdb').read_bytes()).hexdigest()})
    (args.scans/'coordinate_audit.json').write_text(json.dumps({**revisions(),'job_id':os.environ['SLURM_JOB_ID'],
        'tolerances_note':'Allows PDB coordinate rounding: 0.005 A bond/domain RMSD, 0.5 degree bond angle. No thermodynamic validation.',
        'records':results},indent=2)+'\n')


if __name__=='__main__':
    main()
