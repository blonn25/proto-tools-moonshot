"""CPU ray tracing helper; called only inside the managed PyMOL environment."""

import json
import os
import sys
from pathlib import Path

import pymol


def main():
    if not os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("Rendering belongs on a CPU compute node.")
    output = Path(sys.argv[1])
    pymol.finish_launching(["pymol", "-cq"])
    from pymol import cmd
    cmd.set("max_threads", int(os.environ["SLURM_CPUS_PER_TASK"]))
    cmd.bg_color("white")
    cmd.set("ray_opaque_background", 1)
    cmd.set("antialias", 2)
    cmd.set("orthoscopic", 1)
    cmd.set("ray_shadows", 0)
    cmd.set("specular", 0.2)
    cmd.set("cartoon_fancy_helices", 1)
    cmd.set("cartoon_flat_sheets", 1)
    cmd.set("cartoon_smooth_loops", 0)
    cmd.set_color("gate_low", [0, 0.447, 0.698])
    cmd.set_color("gate_high", [0.835, 0.369, 0])
    for name, filename, color in [("low", "1LYA_mapped.pdb", "gate_low"),
                                  ("high", "1LYW_aligned.pdb", "gate_high")]:
        cmd.load(str(output / filename), name)
        cmd.hide("everything", name)
        cmd.show("cartoon", name)
        cmd.color("gray80", name)
        cmd.color(color, f"{name} and chain A and resi 3-16")
        cmd.show("sticks", f"{name} and resi 33+231 and not name N+C+CA+O")
        cmd.color("gray20", f"{name} and resi 33+231 and not name N+C+CA+O")
        cmd.set("stick_radius", 0.22)
    cmd.disable("high")
    cmd.viewport(1800, 1800)
    cmd.orient("low")
    cmd.zoom("low or high", 5)
    view = cmd.get_view()
    cmd.png(str(output / "native_low.png"), width=1800, height=1800, dpi=300, ray=1)
    cmd.disable("low"); cmd.enable("high"); cmd.set_view(view)
    cmd.png(str(output / "native_high.png"), width=1800, height=1800, dpi=300, ray=1)
    (output / "render_provenance.json").write_text(json.dumps({
        "pymol_version": cmd.get_version(), "job_id": os.environ["SLURM_JOB_ID"],
        "view": list(view), "method": "CPU ray trace of experimental structures; shared camera and prior fixed-framework alignment",
        "attribution": "Open-Source PyMOL, Schrodinger, LLC; see upstream copyright notice."}, indent=2) + "\n")
    cmd.quit()


if __name__ == "__main__":
    main()
