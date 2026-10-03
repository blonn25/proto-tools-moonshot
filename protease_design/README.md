# Switchable protease design

The completed computational campaign proposes **ten canonical-L protein candidates**
combining short recombinant cathepsin D with alkaline D-peptidase. The proposed
reversible input is approximately pH 5.0 versus 7.5, qualified experimentally
before use. Initial substrates are matched L- and entirely D-phenylalanine
oligomers. These are experimental candidates, not demonstrated switches.

Thirty-three fusion sequences were screened with ESMFold. Thirteen longer-spacer
candidates received alignment-supported Boltz prediction, restrained geometry
preparation, fixed linker scans, and independent coordinate audits. Ten pass the
combined checks. Structure prediction supports plausible domain folds and steric
feasibility; actual reciprocal activity, off-target cleavage, folding across the
pH window, and production yields remain unmeasured. Test the isolated-parent
activity matrix before scaling production of the complete panel.

- [Paper (PDF)](../data/corehpc/protease_design/manuscript_build/main.pdf) and [LaTeX source](manuscript/main.tex)
- [Ten-design panel and interpretation](designs/README.md), [mature sequences](designs/selected.fasta), and [per-design metrics](designs/selected_metrics.csv)
- [Reproducibility archive](../data/corehpc/protease_design/deliverables/protease_design_report.zip)
- [Literature review](literature_review.md)
- [Progress and job manifest](manifest.md)
- [Design specification](design_specification.md)
- [Sequence-defined production proposal](production_design.md)
- [Fold-preserving characterization plan](characterization_plan.md)
- [Quantitative selectivity requirements](selectivity_framework.md)
- [Development and CoreHPC execution](computational_setup.md)

The direct LC-MS/HPLC assay requires no reporter protein or coupled enzyme.
Isothermal folding checks, soluble recovery, intact-protein analysis, and recovery
of both activities after pH cycles qualify the mild input window. Acidic CatD
maturation occurs separately, before introducing ADP during assembly.

The campaign used no more than two CoreHPC GPUs concurrently, enforced by a
submission guard and checked against SLURM accounting. Bulk structures, exact
alignments, model weights, environments, and outputs remain in ignored
`data/corehpc/protease_design/`; logs remain in `logs/`. The linked PDF/archive
are local deliverables, so a fresh Git clone must restore or rebuild them from
the retained data. Source and small sequence/evidence files are versioned on
`research/protease-chirality-switch`.
