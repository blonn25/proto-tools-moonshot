"""CPU PyMOL ray tracing in the managed environment."""

import json
import os
import sys
from pathlib import Path

import pymol


def main():
    if not os.environ.get('SLURM_JOB_ID'):
        raise SystemExit('Use a CPU allocation.')
    output=Path(sys.argv[1]);meta=json.loads((output/'inputs.json').read_text())
    pymol.finish_launching(['pymol','-cq'])
    from pymol import cmd
    cmd.set('max_threads',int(os.environ['SLURM_CPUS_PER_TASK']))
    cmd.bg_color('white');cmd.set('ray_opaque_background',1);cmd.set('antialias',2)
    cmd.set('orthoscopic',1);cmd.set('ray_shadows',0);cmd.set('specular',0.2)
    cmd.set('cartoon_fancy_helices',1);cmd.set('cartoon_flat_sheets',1);cmd.set('cartoon_smooth_loops',0)
    cmd.set_color('catd_blue',[0,0.447,0.698]);cmd.set_color('adp_orange',[0.835,0.369,0])
    cmd.set_color('gate_purple',[0.65,0.2,0.65])
    names=[r['name'] for r in meta['sources']]
    for name in names:
        cmd.load(str(output/f'{name}.pdb'),name);cmd.hide('everything',name);cmd.show('cartoon',name)
        cmd.color('gray70',name)
        cmd.color('catd_blue',f'{name} and resi 1-{meta["catd_end"]}')
        cmd.color('adp_orange',f'{name} and resi {meta["adp_start"]}-9999')
    cmd.load(meta['native_gate'],'gate');cmd.hide('everything','gate')
    cmd.show('cartoon','gate and chain A and resi 3-16');cmd.color('gate_purple','gate')
    cmd.viewport(1800,1900)
    cmd.orient('boltz_raw and resi 1-354')
    cmd.zoom('all',4);view=cmd.get_view()
    for name in names:
        for other in names:cmd.disable(other)
        cmd.enable(name);cmd.enable('gate');cmd.set_view(view)
        cmd.png(str(output/f'{name}.png'),width=1800,height=1900,dpi=300,ray=1)
    (output/'render_provenance.json').write_text(json.dumps({'job_id':os.environ['SLURM_JOB_ID'],
        'pymol_version':cmd.get_version(),'shared_view':list(view),'method':'CPU ray trace; CatD-framework alignment; inherited model geometry and constructed torsion endpoints, not measured conformations'},indent=2)+'\n')
    cmd.quit()


if __name__=='__main__':
    main()
