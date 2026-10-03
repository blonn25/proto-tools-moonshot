"""Render one candidate's predicted and constructed arrangements with a shared camera."""

import json
import os
import subprocess
from pathlib import Path

import numpy as np

from analyze_structures import ca_positions, fit, read_prediction, read_reference
from execution_provenance import revisions


def main():
    if not os.environ.get('SLURM_JOB_ID'):
        raise SystemExit('Use the CPU SLURM template.')
    from proto_tools.utils import ToolInstance
    base = Path('data/corehpc/protease_design')
    item = next(r for r in json.loads((base/'inputs/round2/candidates.json').read_text())['records'] if r['id']=='CDAD_WT_GS9')
    native = read_reference(base/'references','1LYA','catd')
    positions=ca_positions(native,'catd')
    output=base/'results/rendered_candidate';output.mkdir(exist_ok=True)
    sources=[('boltz_raw','boltz_refined_projected'),('boltz_constructed','linker_scan_boltz_3d'),('esm_constructed','linker_scan_esm_3d')]
    metadata=[]
    for name,directory in sources:
        source=base/'results'/directory/item['id']/'structure.pdb'
        atoms,_,_=read_prediction(source,item['sequence'])
        rotation,translation,_=fit([atoms[p,'CA'] for p in positions],[native[p,'CA'] for p in positions])
        lines=[]
        for line in source.read_text().splitlines():
            if line.startswith('ATOM'):
                xyz=np.array([float(line[j:j+8]) for j in (30,38,46)])@rotation+translation
                line=line[:30]+''.join(f'{x:8.3f}' for x in xyz)+line[54:]
            lines.append(line)
        (output/f'{name}.pdb').write_text('\n'.join(lines)+'\n')
        metadata.append({'name':name,'source':str(source),'source_run':json.loads((source.parent/'run.json').read_text())['structure_sha256']})
    job={'id':item['id'],'catd_end':item['domains']['catd'][1],'adp_start':item['domains']['adp'][0],
         'native_gate':str((base/'results/rendered/1LYW_aligned.pdb').resolve()),'sources':metadata,**revisions()}
    (output/'inputs.json').write_text(json.dumps(job,indent=2)+'\n')
    python=ToolInstance.get('pymol_rmsd').env_path/'bin/python'
    subprocess.run([str(python),str(Path(__file__).with_name('render_candidate_worker.py')),str(output.resolve())],check=True)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from make_figures import save
    plt.rcParams.update({'font.family':'DejaVu Sans','pdf.fonttype':42,'svg.fonttype':'none'})
    fig,axes=plt.subplots(1,3,figsize=(7.1,3.2))
    for ax,(name,_),title in zip(axes,sources,['a  Boltz: local repair only','b  Boltz: constructed pose','c  ESMFold: constructed pose']):
        ax.imshow(plt.imread(output/f'{name}.png'));ax.axis('off');ax.set_anchor('N');ax.set_title(title,fontsize=8,loc='left')
    fig.text(0.5,0.06,'WT GS9. Blue: CatD; orange: ADP; gray: linker.\nPurple: transferred occluded native gate. Constructed poses have no population estimate.',ha='center',fontsize=8)
    fig.tight_layout(rect=(0,0.13,1,1),w_pad=0.2)
    save(fig,base/'results/figures','candidate_arrangements')


if __name__=='__main__':
    main()
