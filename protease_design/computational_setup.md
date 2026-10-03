# Development, execution, and reproducibility

Source and documentation work belongs in the Wynton checkout:
`/wynton/home/rotation/blonn25/disco_lab/proto-tools-moonshot`.
Use the active Python environment for development; the repository's first-time
installation command is `pip install -e ".[dev]"`. Tool environments are managed
by proto-tools, not manually activated. The campaign's lightweight generators
and document build also run locally without loading prediction models.

The prepared computational environment is the CoreHPC mirror's `.venv`, with
the project installed editable. Connect from Wynton using `ssh chpc-login`.
Do not substitute another SSH configuration. The mirror is:
`/mnt/scratch/group/CX500059_DS1/blonnquist/proto-tools-moonshot`.

## Source synchronization

This campaign uses branch `research/protease-chirality-switch`. On Wynton,
the available Git executable is
`/wynton/home/rotation/blonn25/.conda/envs/codex-node/bin/git`.
Commit and push intended changes through GitHub, then pull the same branch on
CoreHPC with `git pull --ff-only`. Inspect local changes first. Never update a
checkout while a running job uses it. The pilot jobs were held while pending
before updates; their executed commits, rather than just submitted commits,
are recorded in the manifest and each result's `run.json`.

For new analyses while jobs still use the main mirror, an isolated detached
Git worktree can live under `data/corehpc/protease_design/checkouts/COMMIT`.
Run its analysis scripts by absolute path through the main mirror's SLURM
template, keeping the working directory, environment, and data in the mirror.
New analysis records distinguish their script commit from the installed
runtime commit. This avoids pulling into an active checkout or rebuilding
managed environments under alternate path names. `git fetch` and creation of
a separate worktree do not replace the running checkout's source files.

## Runtime and offline staging

From the mirror, run `module load CBI` and source
`protease_design/scripts/corehpc_env.sh`. This places all project environments,
weights, caches, temporary files, and logs inside the mirror. Only the login
node has internet access; dependency and weight staging must finish there
before an offline compute job starts. Inference and scientific analyses use
SLURM. GPU jobs load `nvidia-hpc` followed by explicit `nvhpc/26.5` after `CBI`.

The ESMFold and Boltz-2 staging scripts eject the environment definitions via
`ToolInstance.eject_standalone`, select CUDA 12.8 wheels appropriate for the
observed driver, and let proto-tools build the managed environments. No model
is loaded during staging. Exact dependency snapshots are retained under
`data/corehpc/protease_design/`.

```bash
source protease_design/scripts/corehpc_env.sh
.venv/bin/python protease_design/scripts/stage_esmfold.py \
  --torch-spec 'torch==2.10.0' \
  --torch-index https://download.pytorch.org/whl/cu128
.venv/bin/python protease_design/scripts/stage_boltz2.py
```

ESMFold weights are pinned to Hugging Face revision
`75a3841ee059df2bf4d56688166c8fb459ddd97a`; Boltz-2 to
`6fdef46d763fee7fbb83ca5501ccceff43b85607`. Boltz's download orchestration uses
the already managed ESMFold environment's Hugging Face helper; its inference
still runs in its own managed environment. Boltz's upstream runtime requires
the affinity checkpoint to be present even though this project uses only the
structure prediction function. The unused checkpoint is recorded as such.

OpenMM 8.4.0.post2 and its matching `OpenMM-CUDA-12` plugin are additional
project dependencies installed from binary wheels. Restrained minimization
uses CUDA with the original ff14SB and `implicit/obc2.xml` force field;
hydrogen placement uses allocated CPU threads. These are geometry checks, not
molecular dynamics or pH simulations. CPU-only generic OBC2 proved prohibitively
slow. A proposed optimized solvent substitution failed an energy-equivalence
check and is excluded from final analysis. Set `CUDA_CACHE_PATH` and
`OPENMM_CACHE_DIR` inside `data/corehpc/cache/` before submission.

## Submit and monitor

Create `logs/` before submission. Use the guard for every campaign GPU job;
do not call `sbatch` directly for these GPU workloads. The guard reserves
pending as well as running allocations and rejects a third GPU. One invocation
requests exactly one GPU, one node, and one task. The wall-time option precedes
the Python script arguments.

```bash
.venv/bin/python protease_design/scripts/submit_gpu.py --minutes 15 \
  protease_design/scripts/fold_candidates.py \
  data/corehpc/protease_design/inputs/candidates.json --shard 0 --shards 2
.venv/bin/python protease_design/scripts/submit_gpu.py --minutes 15 \
  protease_design/scripts/fold_candidates.py \
  data/corehpc/protease_design/inputs/candidates.json --shard 1 --shards 2
```

The scripts retain completed checkpoints only when their sequence, model,
configuration, and structure hashes agree. If a time limit stops a job, rerun
its exact command through the guard after checking the job state. Do not delete
successful checkpoints. The original Boltz persistent-worker pilot stalled;
the completed runs use `fold_boltz2_cli.py` in the same managed environment,
zero loader workers, and explicit system GCC/G++ to avoid the nvhpc module's
incompatible `CC=nvc`. No library source or installed inference code was patched.
Single-sequence runs are retained as method controls. Their ADP parent fails,
so alignment-supported validation is staged separately:

```bash
# Login node: two public-parent searches, no local heavy computation.
.venv/bin/python protease_design/scripts/stage_domain_msas.py
# Offline SLURM inference; use the current isolated script path when appropriate.
.venv/bin/python protease_design/scripts/submit_gpu.py --minutes 30 \
  protease_design/scripts/fold_boltz2_cli.py \
  data/corehpc/protease_design/inputs/validation_pool.json \
  --msa-dir data/corehpc/protease_design/msas \
  --output data/corehpc/protease_design/results/boltz2_msa
.venv/bin/python protease_design/scripts/submit_gpu.py --minutes 30 \
  protease_design/scripts/refine_geometry.py \
  data/corehpc/protease_design/inputs/validation_pool.json --platform CUDA \
  --output data/corehpc/protease_design/results/esmfold_refined_cuda
```

The two parent alignments come from the hosted ColabFold service via the
repository's remote-search client. Retained A3M files and checksums define the
actual inputs because the public server's database version cannot be pinned.
Fusion MSAs contain unpaired domain homologs with gaps outside each domain;
they supply no evolutionary evidence for an interdomain contact. No MSA server
is contacted from compute nodes, and no structural template is supplied.

CPU jobs are submitted using the CPU template:

```bash
sbatch protease_design/scripts/cpu.slurm \
  protease_design/scripts/analyze_structures.py
squeue -u "$USER"
sacct -j JOB_ID --format=JobID,State,ExitCode,Elapsed
```

Read both `logs/protease_gpu_JOB_ID.out` and `.err`, or the analogous CPU logs.
SLURM completion is required before treating an inference checkpoint as a
successful whole job. A predicted model or successful job does not establish
catalytic function.

## Data, analysis, and paper

`fetch_scaffolds.py` retrieves reference records and hashes. Run
`generate_candidates.py` to reproduce the 24 sequences and five controls.
`prepare_substrates.py` checks explicit L/D stereochemistry and hydrolysis mass
balance under a CPU allocation. `analyze_structures.py` compares predictions
with experimental references; supply `--predictions` and a separate `--output`
to analyze an independent predictor or refined structures without overwriting
the original analysis. `make_figures.py` produces PDF, SVG, and PNG figures.

Collect completed run directories separately from GitHub using `rsync`, creating
the destination parents first. Preserve the `run.json`, structures, metrics,
model metadata, and relevant logs together. Bulk outputs are ignored by Git;
source, methods, bibliography, and progress records are versioned.

For the paper, `stage_document_compiler.py` downloads a pinned, hash-checked
Tectonic binary into project data. Run `build_manuscript.py --allow-downloads`
once on a network-capable development host to stage fonts, then use
`build_manuscript.py` for an offline build. The build assembles a standalone
source directory with figures and records input and PDF hashes. Its output is
`data/corehpc/protease_design/manuscript_build/main.pdf`. The draft uses the
official ICLR 2026 style but explicitly states that it has not been submitted.
