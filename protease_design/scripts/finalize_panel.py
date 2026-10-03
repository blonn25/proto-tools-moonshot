"""Assemble ten reviewed experimental candidates, preserving unresolved risks."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

from prepare_production import production_records


def load_records(path):
    return {r['id']: r for r in json.loads(path.read_text())['records']}


def fasta(records):
    return ''.join('>' + r['id'] + '\n' + '\n'.join(r['sequence'][i:i+80] for i in range(0, len(r['sequence']), 80)) + '\n' for r in records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ids', nargs='+', required=True)
    parser.add_argument('--output', type=Path, default=Path('protease_design/designs'))
    args = parser.parse_args()
    if len(args.ids) != 10 or len(set(args.ids)) != 10:
        raise ValueError('Exactly ten unique reviewed IDs are required.')
    base = Path('data/corehpc/protease_design')
    inputs = [base / 'inputs' / name for name in ['candidates.json', 'round2/candidates.json', 'round3/candidates.json']]
    library = {r['id']: r for p in inputs for r in json.loads(p.read_text())['records']}
    analysis_paths = {name: base / 'results' / directory / 'structural_analysis.json' for name, directory in
                      [('esm', 'analysis_esm_final'), ('boltz_msa', 'analysis_boltz_msa_final'), ('refined', 'analysis_refined_final')]}
    analyses = {k: load_records(p) for k, p in analysis_paths.items()}
    assay = load_records(base / 'results/assay_metadata/assay_metadata.json')
    candidates, table, evidence = [], [], []
    for name in args.ids:
        item = library[name]
        if set(item['sequence']) - set('ACDEFGHIKLMNPQRSTVWY') or hashlib.sha256(item['sequence'].encode()).hexdigest() != item['sequence_sha256']:
            raise ValueError('Sequence identity/canonical-composition check failed.')
        for method in ['esm', 'boltz_msa']:
            row = analyses[method][name]
            for metrics in row['domains'].values():
                if (metrics['resolved_mean_plddt'] < 80 or metrics['framework_rmsd_A'] > 2.5 or
                        metrics['framework_rmsd_delta_from_parent_A'] > 0.75):
                    raise ValueError(f'Domain triage failed: {name}, {method}')
            stereo = row['canonical_stereochemistry']
            if stereo['inverted_centers'] or stereo['degenerate_centers']:
                raise ValueError('Raw prediction has unresolved stereochemistry.')
        repaired = analyses['refined'][name]
        stereo = repaired['canonical_stereochemistry']
        if stereo['inverted_centers'] or stereo['degenerate_centers'] or stereo['minimum_canonical_signed_volume_A3'] < 1.8:
            raise ValueError('Final geometry has unacceptable stereochemistry.')
        if any(not 1.9 < x < 2.2 for x in repaired['domains']['catd']['disulfide_distances_A']):
            raise ValueError('Disulfides need further review.')
        scans = {}
        for method, directory in [('esm', 'linker_scan_esm_3d'), ('boltz_msa', 'linker_scan_boltz_3d')]:
            p = base / 'results' / directory / name / 'geometry_scan.json'
            scan = json.loads(p.read_text())
            if not scan['selected'] or not scan['selected']['geometrically_feasible']:
                raise ValueError(f'No feasible constructed arrangement: {name}, {method}')
            scans[method] = {k: v for k, v in scan.items() if k != 'grid'}
        candidates.append(item)
        summary = {'id': name, 'catd_variant': item['catd_variant'], 'spacer': item['spacer_name'],
                   'length': item['length'], 'monoisotopic_mass_Da_4SS': assay[name]['monoisotopic_mass_expected_disulfides_Da'],
                   'epsilon280_M_inverse_cm_inverse_4SS': assay[name]['epsilon280_oxidized_M_inverse_cm_inverse'],
                   'esm_catd_plddt': analyses['esm'][name]['domains']['catd']['resolved_mean_plddt'],
                   'esm_adp_plddt': analyses['esm'][name]['domains']['adp']['resolved_mean_plddt'],
                   'boltz_catd_plddt': analyses['boltz_msa'][name]['domains']['catd']['resolved_mean_plddt'],
                   'boltz_adp_plddt': analyses['boltz_msa'][name]['domains']['adp']['resolved_mean_plddt'],
                   'refined_catd_rmsd_A': repaired['domains']['catd']['framework_rmsd_A'],
                   'refined_adp_rmsd_A': repaired['domains']['adp']['framework_rmsd_A'],
                   'esm_feasible_grid_points_of1728': scans['esm']['feasible_grid_points'],
                   'boltz_feasible_grid_points_of1728': scans['boltz_msa']['feasible_grid_points'],
                   'sequence_sha256': item['sequence_sha256']}
        table.append(summary)
        evidence.append({'id': name, 'assay_metadata': assay[name],
                         'structural_metrics': {k: v[name] for k, v in analyses.items()}, 'kinematic_feasibility': scans})
    if len({r['sequence'] for r in candidates}) != 10:
        raise ValueError('Duplicate sequences.')
    args.output.mkdir(parents=True, exist_ok=True)
    sources = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs + list(analysis_paths.values())}
    result = {'status': 'Ten candidates proposed for experimental testing; no measured switching, stability, expression, or selectivity.',
              'shared_go_no_go': 'Verify reciprocal parent-domain activity on an exact matched substrate within a fold-preserving pH window before scaling fusion production.',
              'input_sha256': sources, 'records': candidates}
    (args.output / 'selected.json').write_text(json.dumps(result, indent=2) + '\n')
    (args.output / 'selected.fasta').write_text(fasta(candidates))
    (args.output / 'evidence.json').write_text(json.dumps({'records': evidence}, indent=2) + '\n')
    with (args.output / 'selected_metrics.csv').open('w') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table[0])); writer.writeheader(); writer.writerows(table)
    precursor = json.loads((base / 'references/P07339.json').read_text())['sequence']['value']
    production = production_records(candidates, precursor)
    production['status'] = 'Proposed tagged expression intermediates; processing and ligation remain unvalidated.'
    (args.output / 'production.json').write_text(json.dumps(production, indent=2) + '\n')
    for key in ['donors', 'acceptors']:
        (args.output / f'{key}.fasta').write_text(fasta(production[key]))
    rows = []
    for name, item in library.items():
        e = analyses['esm'][name]
        m = analyses['boltz_msa'].get(name)
        rows.append({'id': name, 'selected': name in args.ids, 'length': item['length'],
            'esm_raw_interdomain_atoms_below2A': e['interdomain_contacts']['atoms_a_within_2A'],
            'esm_transferred_occluded_atoms_below2A': e['transferred_catd_states']['1LYW']['atoms_a_within_2A'],
            'boltz_raw_interdomain_atoms_below2A': m['interdomain_contacts']['atoms_a_within_2A'] if m else None,
            'boltz_transferred_occluded_atoms_below2A': m['transferred_catd_states']['1LYW']['atoms_a_within_2A'] if m else None,
            'decision': 'Experimental panel' if name in args.ids else
                'Not advanced: short/helical spacer crowding in initial screen' if item['spacer_name'] not in ['GS5','GS7','GS9','GS11'] else
                'Not selected: raw/refined gate-contact sensitivity; longer alternatives retained'})
    with (args.output / 'all_candidates.csv').open('w') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (args.output / 'assay_record_template.csv').write_text('design_id,preparation_id,replicate,pH,temperature_C,buffer,nominal_intact_enzyme_M,substrate_id,substrate_chirality,substrate_M,time_s,intact_substrate_M,product_identity,product_M,soluble_recovery_fraction,module_L_activity_recovery_fraction,module_D_activity_recovery_fraction,notes\n')


if __name__ == '__main__':
    main()
