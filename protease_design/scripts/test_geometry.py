"""Numerical checks for the structural screen; run with the CPU SLURM template."""

import numpy as np

from analyze_structures import fit, minimum_distance, read_reference


def test_fit_removes_rigid_motion_without_removing_reflection():
    coordinates = np.array([[0., 0., 0.], [1., 0., 0.], [0., 2., 0.], [0., 0., 3.]])
    rotation = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
    transformed = coordinates @ rotation + np.array([3., 5., -2.])
    r, t, deviations = fit(coordinates, transformed)
    assert np.max(deviations) < 1e-10
    assert np.linalg.det(r) > 0.999999
    mirror = coordinates * np.array([-1., 1., 1.])
    _, _, mirror_deviations = fit(coordinates, mirror)
    assert np.sqrt(np.mean(mirror_deviations ** 2)) > 0.1


def test_contacts_count_atoms_not_pairs():
    result = minimum_distance([np.array([0., 0., 0.]), np.array([8., 0., 0.])],
                              [np.array([1., 0., 0.]), np.array([1.5, 0., 0.])])
    assert result["minimum_angstrom"] == 1.0
    assert result["atoms_a_within_2A"] == 1


def test_reference_maps_preserve_known_catalytic_atoms():
    from pathlib import Path
    directory = Path("data/corehpc/protease_design/references")
    adp = read_reference(directory, "4Y7P", "adp")
    assert all(key in adp for key in [(79, "OG"), (82, "NZ"), (176, "OH"), (317, "NE2")])
    for state in ("1LYA", "1LYW"):
        catd = read_reference(directory, state, "catd")
        assert (39, "CG") in catd and (237, "CG") in catd
        # The crystal's excised interchain segment must not shift heavy-chain numbering.
        assert (100, "CA") in catd and (112, "CA") in catd
        assert (105, "CA") not in catd
