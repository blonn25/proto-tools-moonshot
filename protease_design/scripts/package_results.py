"""Create a self-contained, allowlisted report bundle without weights or environments."""

import hashlib
import json
import zipfile
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[2]
    base=root/'data/corehpc/protease_design'
    designs=root/'protease_design/designs'
    selected=json.loads((designs/'selected.json').read_text())['records']
    output=base/'deliverables';output.mkdir(exist_ok=True)
    paths=set()
    for p in (root/'protease_design').rglob('*'):
        if p.is_file() and p.suffix in ['.py','.md','.sh','.slurm','.tex','.bib','.sty','.bst','.json','.csv','.fasta'] and '__pycache__' not in p.parts:
            paths.add(p)
    for relative in ['manuscript_build/main.pdf','manuscript_build/build_provenance.json','job_inventory.json',
                     'esmfold_model.json','boltz2_model.json','project_requirements_resolved.txt']:
        p=base/relative
        if not p.is_file():raise FileNotFoundError(p)
        paths.add(p)
    for directory in ['references','msas','inputs','results/figures']:
        for p in (base/directory).rglob('*'):
            allowed = ['.json','.cif','.pdb','.a3m','.fasta','.csv','.sdf','.smi']
            if directory == 'results/figures':
                allowed += ['.pdf','.png','.svg']
            if p.is_file() and p.suffix in allowed:
                paths.add(p)
    for p in (base/'results').glob('analysis*/*'):
        if p.is_file() and p.suffix in ['.json','.csv']:paths.add(p)
    for directory in ['linker_scan_esm_3d','linker_scan_boltz_3d']:
        paths.add(base/'results'/directory/'coordinate_audit.json')
    methods=['esmfold','boltz2_msa','esmfold_refined_canonical','boltz_refined_projected',
             'linker_scan_esm_3d','linker_scan_boltz_3d']
    for item in selected:
        for method in methods:
            directory=base/'results'/method/item['id']
            for name in ['structure.pdb','run.json']:
                p=directory/name
                if not p.is_file():raise FileNotFoundError(p)
                paths.add(p)
            if method in ['esmfold','boltz2_msa']:
                paths.add(directory/'metrics.json')
            if method.startswith('linker_scan'):
                paths.add(directory/'geometry_scan.json')
    controls=json.loads((base/'inputs/controls.json').read_text())['records']
    for record in controls:
        for method in ['esmfold','boltz2_cli','boltz2_msa']:
            for name in ['structure.pdb','run.json','metrics.json']:
                p=base/'results'/method/record['id']/name
                if not p.is_file():raise FileNotFoundError(p)
                paths.add(p)
    manifest={}
    archive=output/'protease_design_report.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as bundle:
        for p in sorted(paths):
            relative=p.relative_to(root).as_posix()
            data=p.read_bytes()
            manifest[relative]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
            bundle.writestr(relative,data)
        bundle.writestr('BUNDLE_MANIFEST.json',json.dumps({'files':manifest,
            'scope':'Research report, source, exact inputs and alignments, selected coordinates and raw predictor confidence, full analysis summaries. Weights, environments, and caches excluded; reconstruct from pinned staging scripts.',
            'status':'Computational candidates; no experimental validation.'},indent=2)+'\n')
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:raise RuntimeError('Archive CRC verification failed.')
    (output/'bundle_provenance.json').write_text(json.dumps({'archive':archive.name,
        'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,
        'files':len(manifest)},indent=2)+'\n')


if __name__=='__main__':
    main()
