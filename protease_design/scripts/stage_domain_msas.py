"""Stage two public-parent MSAs and build unpaired, gap-padded fusion alignments.

Run network orchestration on the CoreHPC login node. No structural templates,
paired interdomain homologs, or invented fusion homologs are supplied.
"""

import argparse
import hashlib
import json
import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from execution_provenance import revisions


def read_a3m(path, query):
    records = []
    header, chunks = None, []
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        if line.startswith('>'):
            if header is not None:
                records.append((header, ''.join(chunks)))
            header, chunks = line[1:], []
        else:
            chunks.append(line.strip())
    if header is not None:
        records.append((header, ''.join(chunks)))
    if not records or records[0][1] != query:
        raise ValueError(f'MSA query differs from parent: {path}')
    for _, sequence in records:
        aligned = ''.join(x for x in sequence if not x.islower())
        if len(aligned) != len(query) or set(aligned) - set('ACDEFGHIKLMNPQRSTVWYX-'):
            raise ValueError(f'Invalid A3M columns or alphabet: {path}')
    return records


def padded_rows(rows, left, right, prefix):
    return [(f'{prefix}_{i}_{header}', '-' * left + sequence + '-' * right)
            for i, (header, sequence) in enumerate(rows, 1)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, default=Path('data/corehpc/protease_design/inputs'))
    parser.add_argument('--pool', type=Path, default=Path('data/corehpc/protease_design/inputs/validation_pool.json'))
    parser.add_argument('--output', type=Path, default=Path('data/corehpc/protease_design/msas'))
    parser.add_argument('--max-parent-rows', type=int, default=512)
    args = parser.parse_args()
    if os.environ.get('SLURM_JOB_ID'):
        raise SystemExit('Network-dependent staging belongs on the login node.')
    if args.max_parent_rows < 2:
        raise ValueError('At least query and one homolog required.')
    controls = {r['id']: r for r in json.loads((args.inputs / 'controls.json').read_text())['records']}
    parents = [controls['srCatD_WT'], controls['ADP_parent']]
    args.output.mkdir(parents=True, exist_ok=True)
    metadata_path = args.output / 'parents.json'
    if not metadata_path.exists():
        from proto_tools.tools.sequence_alignment.mmseqs2.remote_search import search_remote_msas
        result = search_remote_msas([{'sequences': r['sequence']} for r in parents],
            args.output / 'server', use_metagenomic_db=False,
            client_identity='proto-tools-protease-design', timeout=1200)
        if result['num_successful'] != 2 or result['num_failed']:
            raise RuntimeError(f'Incomplete remote parent search: {result}')
        saved = []
        for i, record in enumerate(parents):
            dest = args.output / f"{record['id']}.source.a3m"
            shutil.copyfile(result['msa_paths'][str(i)], dest)
            rows = read_a3m(dest, record['sequence'])
            saved.append({'id': record['id'], 'sequence_sha256': record['sequence_sha256'],
                          'msa_sha256': hashlib.sha256(dest.read_bytes()).hexdigest(),
                          'returned_rows': len(rows)})
        metadata_path.write_text(json.dumps({**revisions(), 'retrieved_utc': datetime.now(timezone.utc).isoformat(),
            'service': 'https://api.colabfold.com', 'database': 'hosted UniRef; server version not pinned',
            'use_metagenomic_db': False, 'records': saved}, indent=2) + '\n')
    metadata = json.loads(metadata_path.read_text())
    homologs = {}
    for record, provenance in zip(parents, metadata['records']):
        path = args.output / f"{record['id']}.source.a3m"
        if (provenance['sequence_sha256'] != record['sequence_sha256'] or
                provenance['msa_sha256'] != hashlib.sha256(path.read_bytes()).hexdigest()):
            raise ValueError('Parent MSA provenance mismatch.')
        rows = read_a3m(path, record['sequence'])
        seen, keep = {record['sequence']}, []
        for header, sequence in rows[1:]:
            if sequence not in seen:
                keep.append((header, sequence)); seen.add(sequence)
            if len(keep) == args.max_parent_rows - 1:
                break
        homologs[record['id']] = keep
    pool = json.loads(args.pool.read_text())['records']
    pilot = json.loads((args.inputs / 'validation_pilot.json').read_text())['records']
    candidates = {r['id']: r for r in pool + pilot}
    entries = []
    for record in candidates.values():
        rows = [(record['id'], record['sequence'])]
        if record['kind'] == 'fusion':
            start = record['domains']['adp'][0] - 1
            rows += padded_rows(homologs['srCatD_WT'], 0, record['length'] - 354, 'catd')
            rows += padded_rows(homologs['ADP_parent'], start, 0, 'adp')
        else:
            parent = 'ADP_parent' if record['id'] == 'ADP_parent' else 'srCatD_WT'
            rows += padded_rows(homologs[parent], 0, 0, parent)
        path = args.output / f"{record['id']}.a3m"
        path.write_text(''.join(f'>{h}\n{s}\n' for h, s in rows))
        read_a3m(path, record['sequence'])
        entries.append({'id': record['id'], 'rows': len(rows), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    (args.output / 'assembly.json').write_text(json.dumps({**revisions(),
        'method': 'First distinct rows in server order, capped per parent; homolog rows gap-padded outside their domain. Query substitutions applied only to query row. No paired interdomain evolutionary information.',
        'max_parent_rows': args.max_parent_rows, 'records': entries}, indent=2) + '\n')
    logging.info('Prepared %d alignments from two public-parent searches.', len(entries))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
