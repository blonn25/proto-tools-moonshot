"""Signed-volume checks for canonical alpha and Ile/Thr beta stereocenters."""

import numpy as np


def volume(points):
    center, a, b, c = np.asarray(points)
    return float(np.dot(a - center, np.cross(b - center, c - center)))


def centers(sequence):
    for p, residue in enumerate(sequence, 1):
        if residue != 'G':
            yield p, 'alpha', ('CA', 'N', 'C', 'CB')
        if residue == 'T':
            yield p, 'thr_beta', ('CB', 'CA', 'OG1', 'CG2')
        if residue == 'I':
            yield p, 'ile_beta', ('CB', 'CA', 'CG1', 'CG2')


def reference_signs(references):
    values = {'alpha': [], 'thr_beta': [], 'ile_beta': []}
    for atoms in references.values():
        for p in {p for p, atom in atoms if atom == 'CA'}:
            groups = [('alpha', ('CA', 'N', 'C', 'CB'))]
            if (p, 'OG1') in atoms:
                groups.append(('thr_beta', ('CB', 'CA', 'OG1', 'CG2')))
            if (p, 'CG1') in atoms and (p, 'CD1') in atoms:
                groups.append(('ile_beta', ('CB', 'CA', 'CG1', 'CG2')))
            for kind, names in groups:
                if all((p, a) in atoms for a in names):
                    values[kind].append(volume([atoms[p, a] for a in names]))
    signs = {}
    for kind, data in values.items():
        if not data:
            raise ValueError(f'No experimental stereochemistry calibration: {kind}')
        sign = int(np.sign(np.median(data)))
        if sign == 0 or np.mean(np.sign(data) == sign) < 0.99:
            raise ValueError(f'Inconsistent native stereochemistry: {kind}')
        signs[kind] = sign
    return signs


def audit(atoms, sequence, signs):
    values, inverted, degenerate = [], [], []
    for p, kind, names in centers(sequence):
        v = signs[kind] * volume([atoms[p, a] for a in names])
        values.append(v)
        if abs(v) < 0.1:
            degenerate.append({'position': p, 'kind': kind})
        elif v < 0:
            inverted.append({'position': p, 'kind': kind})
    return {'inverted_centers': inverted, 'degenerate_centers': degenerate,
            'minimum_canonical_signed_volume_A3': min(values),
            'checked_centers': len(values), 'reference_signs': signs}
