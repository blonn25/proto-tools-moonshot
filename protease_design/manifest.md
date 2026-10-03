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

Phase: computational design and ten-candidate selection complete; manuscript
and reproducibility package undergoing final assembly and verification.

All 33 fusions and five controls have ESMFold results. Thirteen long-spacer
fusions received alignment-supported Boltz validation, canonical geometry
preparation with both predictors, and fixed 1,728-point linker scans. Ten pass
all domain, stereochemistry, disulfide, geometric-feasibility, and independent
coordinate checks. Selected sequences and production intermediates are in
`designs/`. Single-sequence Boltz's failed ADP control, unfavorable raw domain
placements, and rejected preparation attempts remain in the record.

The ICLR-format manuscript compiles to 16 pages including references and
appendices; main text occupies eight pages. No experimental activity, stability,
production, or switching measurements exist. Reciprocal parent-domain activity
on the exact matched substrates in a qualified pH window is the shared early
experimental decision. Y10F GS9 and D187N GS7 are particularly sensitive to the
limited Boltz-derived geometry grid.

SLURM accounting confirms at most two campaign GPUs allocated concurrently and
2.053 allocated GPU-hours, including failed/cancelled allocated GPU runs.
Final coordinate checks and figure rendering use only CPU jobs. No campaign
job remains running after their completion.

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
| 2111024 | `16406443` | 4 CPUs, 16 GB | Generic OBC2 WT srCatD pilot | CANCELLED after slow force evaluation; 55 min 6 s |
| 2111025 | `16406443` | 4 CPUs, 16 GB | Generic OBC2 WT GS3 pilot | CANCELLED after slow force evaluation; 55 min 6 s |
| 2111026 | `16406443` | 4 CPUs, 16 GB | Partial enhanced structure analysis | COMPLETED, exit 0; 8 s |
| 2111226 | script `44b8c4f9`, runtime `16406443` | 4 CPUs, 16 GB | Complete first-screen analysis | COMPLETED, exit 0; 12 s |
| 2111227 | script `44b8c4f9`, runtime `16406443` | 4 CPUs, 16 GB | Experimental-state ray tracing | COMPLETED, exit 0; 14 s |
| 2111325 | script `951fe6d0`, runtime `16406443` | 1 GPU, 4 CPUs, 64 GB | Boltz upstream-CLI pilot | FAILED, exit 1; 54 s; nvc rejects Triton compiler flag |
| 2111366 | script `20f3f669`, runtime `16406443` | 1 GPU, 4 CPUs, 64 GB | Eight second-round ESMFold fusions | COMPLETED, exit 0; 5 min 29 s |
| 2111431 | script `79300408`, runtime `16406443` | 4 CPUs, 16 GB | Shared-camera structural renderings | COMPLETED, exit 0; 11 s |
| 2111452 | script `79300408`, runtime `16406443` | 4 CPUs, 16 GB | Updated composite/vector figures | COMPLETED, exit 0; 7 s |
| 2111453 | script `20f3f669`, runtime `16406443` | 4 CPUs, 16 GB | Combined first/second-round analysis | COMPLETED, exit 0; 10 s |
| 2111464 | script `70d71b76`, runtime `16406443` | Requested 1 CPU, 4 GB | Short minimization diagnostic | CANCELLED at 8 min 43 s; generic GB force bottleneck |
| 2111578 | script `74198b9c`, runtime `16406443` | 4 CPUs, 8 GB | Optimized OBC2 parent pilot | Computation completed; 472.6 s refinement; diagnostic only |
| 2111579 | script `74198b9c`, runtime `16406443` | 4 CPUs, 8 GB | Optimized OBC2 WT GS3 pilot | FAILED equivalence check, exit 1; 46 s |
| 2111629 | script `8c410d0e`, runtime `16406443` | 1 GPU, 4 CPUs, 64 GB | Boltz CLI with GCC | COMPLETED, exit 0; 2 min 29 s |
| 2111630 | script `8c410d0e`, runtime `16406443` | 4 CPUs, 8 GB | Reference-precision OBC equivalence | FAILED, exit 1; 2 min 20 s; 7.89 kJ/mol discrepancy |
| 2111743 | script `17356de4`, runtime `16406443` | 1 GPU, 4 CPUs, 64 GB | Original XML OBC2 CUDA pilot | COMPLETED, exit 0; 1 min 15 s |
| 2111744 | script `17356de4`, runtime `16406443` | 4 CPUs, 16 GB | Assay metadata for 37 sequences | COMPLETED, exit 0; 1 s |
| 2111796 | script `17356de4`, runtime `16406443` | 1 GPU, 4 CPUs, 64 GB | Single-sequence Boltz validation pool | RUNNING at last check |
| 2111797 | script `17356de4`, runtime `16406443` | 1 GPU, 4 CPUs, 64 GB | Original XML OBC2 CUDA validation pool | PENDING at last check |
| 2111798 | script `17356de4`, runtime `16406443` | 4 CPUs, 16 GB | Boltz pilot analysis | Output complete; scheduler verification pending |
| 2111799 | script `17356de4`, runtime `16406443` | 4 CPUs, 16 GB | CUDA-refined pilot analysis | Output complete; scheduler verification pending |


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

### 2026-10-03 Numerical and runtime diagnostics

Boltz's direct CLI proceeded beyond the earlier worker stall, then failed in
Triton JIT because the nvhpc module's `CC=nvc` rejects `-Wno-psabi`. A targeted
retry selects system GCC/G++ and explicitly keeps Triton, Inductor, and CUDA
caches inside the mirror. No package/environment source was patched.

The short OpenMM diagnostic completed hydrogen placement and initial energy
evaluation, but remained inside minimization. A native stack localized the
slow calculation to `CpuCustomGBForce`; the cause of its extreme runtime is
not established. Stop these trials rather than count them as completed results.
The one-CPU diagnostic also exposed two srun processes despite the nominal
single-task allocation. The CPU template now explicitly specifies one node,
one task, and `srun --ntasks=1`. Original four-CPU runs showed one process each.

The optimized OBC2 mapping preserved charges, offset/scaled radii, dielectric
constants, surface term, and no cutoff. Parent CPU solvent-energy differences
were 0.053--0.054 kJ/mol; the fusion differed by 0.238--0.245 kJ/mol and correctly
failed the predeclared 0.1 kJ/mol equivalence bound. The next diagnostic compares
both implementations using the double-precision Reference platform, retaining
the same bound, to distinguish parameter differences from CPU arithmetic.
No failed fusion refinement is accepted or silently given a relaxed threshold.

### 2026-10-03 Completed second round and successful CUDA refinement

All eight GS7/GS9 ESMFold proposals preserve both native-like domain folds and
accommodate both transferred CatD states without sub-2 Å interdomain contacts.
Seven raw predictions are clash-free by this criterion; D187N GS7 has one
1.896 Å contact involving a CatD residue with pLDDT 59. Combined with the two
initial GS5 models, this gives nine raw clash-free proposals and a tenth to
review, rather than ten selected enzymes. Interdomain PAE remains about 26 Å.

The optimized solvent substitution failed even with double-precision Reference
energies (approximately 7.894 kJ/mol discrepancy). Abandoned that substitution
for final evaluation; its completed parent run is diagnostic only. Installed
OpenMM's matching CUDA plugin in the project environment, retaining the
original ff14SB/OBC2 XML force field. GPU pilot 2111743 completed in 75 seconds.
CatD parent S--S distances become 2.033--2.038 Å; WT GS3 distances become
2.016--2.038 Å and its minimum interdomain separation becomes 2.642 Å. Domain
framework RMSDs remain below 1 Å. This is restrained geometry repair with
fixed preparation protonation, not molecular dynamics or a pH-switch simulation.

Boltz's explicit-GCC CLI retry completed all three pilot inputs. CatD WT agrees
with the experimental structure (0.705 Å RMSD, 95.65 mean pLDDT), but the native
ADP control fails (22.09 Å, 32.15 pLDDT); fusion ADP likewise fails. Single-sequence
Boltz results cannot validate or reject the proposed ADP domain. The upstream
documentation discourages empty MSAs. Prepare two public-parent alignments from
the ColabFold service, cap distinct homologs at 511 per parent, and gap-pad
domain rows into the fusion sequence without inventing paired interdomain
homology. Use the exact variant sequence only in each query row. This is an
explicit method amendment motivated by a failed positive control; retain the
single-sequence outputs and do not pool their scores with MSA-supported runs.

### 2026-10-03 Alignment control recovery and stereochemistry correction

Two public-parent searches returned 7,889 CatD and 5,744 ADP alignment rows;
retained distinct homologs are capped at 511 per parent. Alignment-supported
Boltz pilot 2111896 completed in 2 min 24 s. ADP now has 0.669 Å framework RMSD
and 92.99 mean resolved pLDDT; CatD WT has 0.629 Å and 88.70. This resolves the
failed no-alignment ADP method control, without establishing fusion function.
Parent searches, exact A3M files, hashes, and assembly metadata are retained.

The original CUDA refinement completed the 17-record pool in job 2111797
(7 min 27 s). Independent analysis exposed inverted alpha centers in Y10F GS5
(Thr586) and E180Q GS9 (Asp158, Thr606). These first-pass refined structures
are excluded from final acceptance. All 37 original ESMFold predictions pass
the expanded audit of alpha and Ile/Thr beta centers. Added a canonical
signed-volume wall, calibrated to experimental reference geometry, and a final
coordinate-level check. New results go in `esmfold_refined_chiral`; original
and unsuccessful outputs remain available. No fold/stability claim follows
from repair. A high-pH transferred-state contact in D187N GS7 still requires
review before a final ten can be justified.

New jobs: 2111935 (stereochemistry-preserving pool refinement), 2111936
(MSA-pilot analysis), 2111937 (37-record expanded stereochemistry audit),
2111943 (MSA-supported validation pool), and 2111944 (dependent refinement
analysis), all at script `39631035`, runtime `16406443`, except the MSA pilot
itself at `e02fdef6`. GPU jobs remain serialized through the aggregate guard.

### 2026-10-03 Geometry acceptance tightening and targeted spacer amendment

The first canonical-volume wall removed inversions but allowed a few centers
to flatten to 0.94--0.97 Å³, well below native-like tetrahedral volumes.
Those coordinates are not accepted as final. Raise the flat-bottom minimum
from 1 to 2 Å³ and require every final center to exceed 1.8 Å³. Retain the
same physical force field and C-alpha restraints; write a separate final
preparation directory. This is a geometry-quality correction, not a relaxed
acceptance criterion. D187N GS7 still has two transferred-occluded-state
contacts below 2 Å. A prospectively recorded third round adds only D187N GS11
as a longer-spacer alternative; all earlier results remain in the record.

### 2026-10-03 Orthogonal domain recovery but unresolved domain placement

MSA-supported pool job 2111943 completed in 12 min 32 s; analysis 2111967
completed in 6 s. All 12 long-spacer fusions retain both native-like domains:
CatD mean pLDDT 82.4--84.5, ADP 86.3--88.6, and domain RMSDs below 1.1 Å.
However, all MSA-derived placements clash with transferred CatD states.
This disagreement is retained, not averaged away. High interdomain PAE means
neither predictor establishes the actual domain arrangement. A prospectively
described, fixed two-torsion grid will test kinematic feasibility for both
predictors while preserving domain geometry. Its outputs cannot establish
favorable conformational populations, minimal leakage, or pH switching.

### 2026-10-03 Finite-grid audit and energy-check diagnostic

The expanded ESMFold scan completed (2112287, 9 min 36 s), followed by its
independent coordinate audit (2112378, 17 s). Boltz preparation 2112286 failed
at Y10F GS7 after eight minutes: its initial energy was anomalously negative
(about -26.4 million kJ/mol), and the finite/energy-descent check rejected the
result. No accepted coordinates were written for that record. Its dependent
jobs remain unrun. Investigate whether comparing an unconstrained starting
energy with a constrained minimum caused this rejection: project initial
H-bond constraints before evaluating the starting energy, and retain both
energies plus failure coordinates. This is a diagnostic hypothesis until the
retry gives actual results; no threshold is relaxed.

### 2026-10-03 Correct constrained-energy baseline

Diagnostic 2112450 completed in 1 min 7 s. In that retry, the unconstrained
energy was -105,187.22 kJ/mol, the constraint-projected starting energy
261,762.13 kJ/mol, and the final constrained energy -89,434.70 kJ/mol. The old
comparison would reject even this geometrically valid result. Explicit initial
constraint projection supplies a comparable baseline; no energy or geometry
threshold was relaxed. The final minimum canonical volume is 2.170 Å³, and
C-alpha displacement is 0.288 Å. This does not establish why the earlier
hydrogen preparation produced the much more negative -26.4-million value.
Remaining Boltz records are being prepared in a separate `boltz_refined_projected`
directory, retaining old successful and rejected attempts. Failed-dependency
jobs 2112318, 2112319, and 2112379 were cancelled; no other user's job was touched.

The completed ESM three-angle scan contains 429--782 feasible points of 1,728
per tested fusion. All 13 independent coordinate audits passed: maximum bond
length change 0.001365 Å and maximum bond-angle change 0.107 degrees, compatible
with PDB rounding. These are geometric checks, not conformational probabilities.

### 2026-10-03 Final panel and exported-coordinate verification

Projected-baseline Boltz preparation finished the remaining records in job
2112465. CPU shards 2112489--2112492 completed the three-angle scan, and audit
2112632 checked its constructed coordinates. Ten of thirteen Boltz-derived
models pass the finite grid; WT GS5, E180Q GS5, and D187N GS5 do not. All thirteen
ESMFold-derived models pass, so the intersection defines the final ten.
Y10F GS9 has one feasible Boltz grid point and D187N GS7 eight; neither count
is a thermodynamic population. Their sensitivity is retained in the panel notes.

Finalizer checks all five parent controls, raw domain criteria, prepared
stereochemistry/disulfides, exact unique canonical sequences, audit hashes,
and donor/acceptor assembly. CPU jobs 2112845 and 2112846 independently reanalyzed
exported ESM/Boltz endpoints after PDB rounding: all twenty selected structures
retain no sub-2 Å interdomain or transferred-state contact and clear the
representative catalytic markers. Four donors and four acceptors supply all ten
mature sequences; their expression and assembly remain proposed.

Figure job 2112686 completed in 21 seconds. The completed manuscript includes
the actual method-control failure/recovery, raw-pose disagreement, rejected
numerical preparations, ten-sequence panel, methods, characterization plan,
and exact sequences. Layout and citations are being checked; the archive will
include file hashes, exact alignments, selected coordinates, raw confidence,
full-library analysis, and environment/model provenance without bulky weights.
