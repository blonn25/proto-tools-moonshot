# Protease design progress manifest

## Objective and constraints

- Produce ten all-canonical-L-amino-acid protein designs for switching between
  L-peptide and all-D-peptide cleavage with minimal opposite-chirality activity.
- Select substrates, conditions, architecture, trigger, and reversibility from
  the literature and computational evidence.
- Complete an extensive literature review before candidate design.
- Deliver a reproducible computational package and ICLR-format manuscript with
  publication-quality figures. Do not imply experimental validation.
- Use no more than two CoreHPC GPUs concurrently across all campaign jobs.
- For pH switching, preserve the folds of the protease and required assay
  proteins; provide simple stability and recovery checks before functional assays.
- Use SLURM for expensive computation; stage network dependencies on login nodes.
- Preserve unrelated user changes and synchronize source through GitHub before
  CoreHPC execution.

## Current status

Phase: literature review and the complete first structure screen finished;
second-round and independent predictions are queued, and geometry checks are running.

Generated 24 initial fusion sequences and five isolated-domain controls from
the prospective specification. All 29 have now been predicted with ESMFold.
The final ten have not been selected. Domain preservation alone is insufficient:
several predictions have severe interdomain loop clashes, and their relative
domain orientation is uncertain (approximately 25 Å interdomain PAE).
Hardware-probe job 2110367 completed successfully at commit `5ce12e48` on an
RTX PRO 6000 Blackwell Server Edition (97,887 MiB; driver 595.71.05).
The project `.venv` and editable development dependencies are installed.
Managed ESMFold environment/weight staging completed on the login node:
PyTorch 2.10.0 with CUDA 12.8 and transformers 5.12.1; model revision
`75a3841ee059df2bf4d56688166c8fb459ddd97a`. CPU geometry checks passed.
All five controls have framework RMSD below 0.9 Å and mean resolved-domain
pLDDT above 87.9. Boltz-2 environment and weights are staged and a three-protein
pilot is running. CPU OpenMM geometry checks are running for the WT parent and
WT GS3 fusion. A nine-page ICLR-format draft compiles, with unfinished computations explicitly
identified; the final results and figures are still being assembled.
No experimental work has been performed.

## Work plan

1. Review natural L-protein catalysts for all-D substrates, stereospecificity,
   switchable proteases, experimentally supported gating, and design evaluation.
2. Select architecture and substrate panels; define quantitative acceptance
   criteria, controls, and limitations before screening.
3. Retrieve verified sequences and experimental structures; prepare reproducible
   design and evaluation scripts and the CoreHPC project environment.
4. Generate and evaluate candidates, including both chirality states, and retain
   ten only when the evidence justifies experimental testing.
5. Produce a methods-complete ICLR-format manuscript, figures, sequence files,
   and an experimental characterization plan tied to actual computations.

## Initial repository and infrastructure observations

- Initial local and CoreHPC revision: `8f803c1c` on `main`.
- Existing local change: CoreHPC guidance in `CLAUDE.md`; preserved.
- `AGENTS.md` is a symlink to `CLAUDE.md`.
- SSH alias `chpc-login` was verified in the preceding repository exploration.
- CoreHPC `CBI`, `nvidia-hpc`, and `nvhpc/26.5` module loads were verified on
  the login node. Runtime verification on compute nodes remains outstanding.
- The default Python environments do not have proto-tools installed. A prepared
  project Python environment has not yet been established.
- The example `.venv`, `data/corehpc/`, and `logs/` paths were absent.

## Activity log

### 2026-10-02 Project initialization

Recorded the user's clarified constraints and added the aggregate two-GPU limit
to `CLAUDE.md`, visible through `AGENTS.md`. Initialized this manifest and the
literature-review document. No source synchronization or computation has yet
occurred. The next step is primary-literature research before design decisions.

### 2026-10-02 Literature synthesis and architecture selection

Reviewed more than twenty primary studies/data records on D-peptide catalysis,
pepsinogen activation and fusion expression, protein switching, and enzyme
design. Saved the synthesis in `literature_review.md` before candidate generation.
Initially selected an ADP–linker–porcine-pepsinogen fusion hypothesis with irreversible
acid-triggered D-to-L switching. Proposed pH 7.9 and 2.5 at approximately 25 °C
are starting conditions for experiments, not measured switching optima.
This choice is superseded by the folding constraint recorded below.

Next: verify experimental scaffold sequences and numbering, define screening
criteria, and prepare reproducible CoreHPC execution. No candidate sequences or
campaign SLURM jobs exist yet.

### 2026-10-02 Fold-preserving trigger revision and infrastructure checks

The user requested a characterization strategy that avoids unfolding the
protease or required assay proteins. Removed pH 2.5 activation from the leading
proposal: stability of the D module at that pH is unsupported. Investigating
cathepsin D's experimentally observed reversible active-site occlusion at pH 7.5
(Lee et al., 1998; PDB 1LYW) as an alternative L module, with an initial pH 5–7.5
window. ADP retains activity after incubation at pH 5–10 in its original study;
its instantaneous activity at pH 5 and the fusion's stability remain unmeasured.

Downloaded experimental reference structures/sequence records 4Y7P, 3PSG, 4PEP,
and 1EI5 with URL and SHA256 provenance in ignored project data. Added CPU/GPU
SLURM templates and a serialized GPU submission guard that reserves pending as
well as running campaign allocations. Five meaningful guard checks passed;
shell syntax and whitespace checks passed. No jobs have been submitted.

### 2026-10-02 Source synchronization and recombinant scaffold evidence

Created branch `research/protease-chirality-switch` and synchronized initial
campaign commit `c4038812` through GitHub to CoreHPC. Staged only the new campaign
section of `CLAUDE.md`; the user's pre-existing CoreHPC guidance remains a local
change. Began project `.venv` installation with editable dev dependencies,
using mirror-local caches and logs. No tool-specific environments were manually
created.

Goldfarb et al. (2005) directly studied pH switching in short recombinant
cathepsin D and characterized four point substitutions. This resolves the
earlier concern that only tissue-derived mature protein supports the mechanism.
Separate domain preparation followed by sortase ligation is being evaluated
to keep ADP out of acidic maturation. Downloaded 1LYA/1LYW and UniProt P07339/
P94288 reference records. A numbering discrepancy requires care: ADP's PDB
author-number offset is not a verified signal-peptide boundary. The 2015
experimental expression construct removed 25 N-terminal residues; its activity
was confirmed. Use that documented construct rather than a predicted cleavage.

### 2026-10-02 Prospective library generation

Defined the screen and acceptance targets in `design_specification.md` before
generation. Executed `python protease_design/scripts/generate_candidates.py`:
24 fusion sequences (four supported L-domain sequences × six spacers) and five
isolated-domain controls were written under ignored `data/corehpc/protease_design/inputs/`.
All sequences pass canonical-residue and catalytic-numbering checks. No
structural or functional scores have yet been assigned. Added an offline
ESMFold runner with input/model/commit provenance and per-sequence checkpoints.

## Job ledger

| Job | Commit | Resources | Purpose | Status |
| --- | --- | --- | --- | --- |
| 2110367 | `5ce12e48` | 1 GPU, 8 CPUs, 96 GB | Hardware/module probe | COMPLETED, exit 0; 1 s |
| 2110560 | `0eebbd1a` executed | 1 GPU, 4 CPUs, 64 GB | Five isolated-domain ESMFold controls | COMPLETED, exit 0; 1 min 43 s |
| 2110561 | `0eebbd1a` executed | 1 GPU, 4 CPUs, 64 GB | WT GS3 fusion ESMFold pilot | COMPLETED, exit 0; 1 min 20 s |
| 2110562 | `e1111525` | 4 CPUs, 16 GB | Geometry and residue-map checks | COMPLETED, exit 0; 3 passed |
| 2110563 | `e1111525` | 4 CPUs, 16 GB | Native CatD state comparison | COMPLETED, exit 0; 3 s |
| 2110770 | `0eebbd1a` | 4 CPUs, 16 GB | Explicit L/D peptide chemistry and mass balance | COMPLETED, exit 0; 2 s |
| 2110771 | `0eebbd1a` | 4 CPUs, 16 GB | Original vector figures | COMPLETED, exit 0; 6 s |
| 2110800 | `0eebbd1a` | 4 CPUs, 16 GB | Parent prediction versus crystal comparison | COMPLETED, exit 0; 2 s |
| 2110847 | `1824ce2f` | 1 GPU, 4 CPUs, 64 GB | ESMFold fusion shard 0 | COMPLETED, exit 0; 14 min 1 s |
| 2110848 | `16406443` executed | 1 GPU, 4 CPUs, 64 GB | ESMFold fusion shard 1 | COMPLETED, exit 0; 6 min 47 s |
| 2111023 | `16406443` | 1 GPU, 4 CPUs, 64 GB | Boltz-2 persistent-worker pilot | CANCELLED after stall; 17 min 57 s |
| 2111024 | `16406443` | 4 CPUs, 16 GB | Restrained WT srCatD geometry repair | RUNNING at last check |
| 2111025 | `16406443` | 4 CPUs, 16 GB | Restrained WT GS3 geometry repair | RUNNING at last check |
| 2111026 | `16406443` | 4 CPUs, 16 GB | Partial enhanced structure analysis | COMPLETED, exit 0; 8 s |
| 2111226 | script `44b8c4f9`, runtime `16406443` | 4 CPUs, 16 GB | Complete first-screen analysis | COMPLETED, exit 0; 12 s |
| 2111227 | script `44b8c4f9`, runtime `16406443` | 4 CPUs, 16 GB | Experimental-state ray tracing | COMPLETED, exit 0; 14 s |
| 2111325 | script `951fe6d0`, runtime `16406443` | 1 GPU, 4 CPUs, 64 GB | Boltz upstream-CLI pilot | PENDING at last check; wall time resized to 30 min |
| 2111366 | script `20f3f669`, runtime `16406443` | 1 GPU, 4 CPUs, 64 GB | Eight second-round ESMFold fusions | PENDING at last check |
| 2111431 | script `79300408`, runtime `16406443` | 4 CPUs, 16 GB | Shared-camera structural renderings | Submitted |

### 2026-10-02 Initial structural analysis

The fixed-framework superposition of 1LYA and 1LYW gives 1.918 Å C-alpha RMSD
and a maximum observed N-terminal gate displacement of 29.987 Å. This is a
reanalysis of experimental structures, not a prediction for the fusion or a
measurement of switching kinetics. Raw results are in ignored
`data/corehpc/protease_design/results/analysis/structural_analysis.json`.
The numerical checks verify rigid alignment without reflection, contact-count
interpretation, and experimental residue mapping across CatD's chain break.

### 2026-10-02 Successful pilot computations and manuscript preparation

The GPU pilot ran on an L40S with 46,068 MiB. All five isolated controls finished
in 103 seconds including model startup; WT GS3 finished in 80 seconds. Control
framework RMSDs were ADP 0.891 Å and srCatD variants 0.682–0.689 Å. Mean
resolved-domain pLDDT was 94.27 for ADP and 87.93–89.13 for srCatD. These are
predicted structures compared with native references, not catalytic measurements.

Pending pilot jobs were explicitly held before two source updates, and released
after each pull; no source was pulled while they ran. Consequently their actual
executed commit is `0eebbd1a`, differing from the original submission revision.
Their requests were reduced before starting to 4 CPUs, 64 GB, and 10 minutes,
improving backfill eligibility. The guard now accepts a bounded wall-time option
and explicitly requests one GPU, one node, and one task.

The Boltz-2 environment installed successfully. The first weight-staging attempt
failed because its inference environment has no Hugging Face Hub package. The
staging script now uses the already managed ESMFold environment's download
helper; no inference implementation or installed environment was patched.
The retry is in progress. Downloaded official ICLR style files and 27 DOI
metadata records, with provenance. The manuscript draft builds using a scoped
Tectonic compiler and Times-compatible fonts. Generated three original figure
sets as PDF/SVG/PNG; no synthetic experimental curves are presented.

## Decisions and unresolved questions

### 2026-10-03 Full screen and independent-predictor troubleshooting

All 24 ESMFold fusion predictions completed; analysis job 2111226 at isolated
source revision `44b8c4f9` (runtime checkout `16406443`) found no missing records.
All four GS5 constructs accommodate both transferred CatD states without
sub-2 Å interdomain contacts. Only WT GS5 and Y10F GS5 are themselves free of
such contacts in the raw prediction. Relative domain PAE is 25.0–26.3 Å, so the
predicted domain orientation is not treated as established. The four GS5
constructs are promising geometries, not an already selected final panel.

PyMOL staging succeeded; CPU rendering job 2111227 completed in 14 seconds.
The main CoreHPC checkout remains fixed at `16406443` while its jobs run.
Analysis scripts use isolated worktrees inside the mirror and record both
script and runtime revisions. Thirty bibliography metadata records are staged.

Boltz pilot 2111023 stalled after preprocessing, with two idle child processes,
0% GPU utilization and approximately 42 seconds of CPU use after more than
15 minutes elapsed. Cancelled only this campaign job after 17 min 57 s to release its GPU.
Forked-loader deadlock is a hypothesis, not a proven root cause. Preparing a
direct upstream CLI retry in the same managed environment, with zero loader
workers and single-thread CPU libraries. The typed wrapper currently requires
at least one loader worker; neither its source nor the managed environment is
patched. Raw CLI outputs and exact command/configuration will be retained.

Recovered Beyer & Dunn (1996), Table I, which specifies the short-form
maturation region `IAKGPVSKPIEFFRLVTEGPIPE`, with cleavage between the paired
phenylalanines. This resolves the engineered local junction, permitting a
sequence-defined production proposal. Proposed vector context and appended
ligation tags remain new engineering choices and require experimental checking.

Added an explicit second-round amendment before its predictions: test GS7 and
GS9 spacers across the same four CatD variants, motivated by the initial GS5
geometry. These eight adaptive proposals supplement, rather than replace, the
original 24. The mature sequences remain separate from the newly specified
expression intermediates. Boltz CLI retry job 2111325 is pending, reserving one
of the two permitted GPUs.

## Open decisions

- Selectivity means avoiding the opposite substrate chirality; the user did not
  prescribe a numerical threshold.
- The entire protein must be genetically expressible using canonical L residues.
  A chemically synthesized mirror-image D-protease is excluded.
- A specific substrate and multidomain or multicomponent architecture are allowed.
- Whether sufficient evidence can support ten switchable designs remains an open
  research question, not an assumed successful outcome.
