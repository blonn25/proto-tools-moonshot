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

Phase: initial literature review completed; revising the trigger to preserve
protein folding, with scaffold verification and runtime preparation underway.

Generated 24 initial fusion sequences and five isolated-domain controls from
the prospective specification. None have been structurally evaluated or selected.
No campaign SLURM jobs have been
submitted. Campaign GPU allocation: 0. No experimental work has been performed.
CoreHPC project dependency installation is underway on the login node.

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

No jobs submitted.

## Decisions and unresolved questions

- Selectivity means avoiding the opposite substrate chirality; the user did not
  prescribe a numerical threshold.
- The entire protein must be genetically expressible using canonical L residues.
  A chemically synthesized mirror-image D-protease is excluded.
- A specific substrate and multidomain or multicomponent architecture are allowed.
- Whether sufficient evidence can support ten switchable designs remains an open
  research question, not an assumed successful outcome.
