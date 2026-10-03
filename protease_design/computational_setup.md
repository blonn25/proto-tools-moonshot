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

OpenMM 8.4.0.post2 is an additional project dependency for CPU geometry checks,
installed from a binary wheel. The geometry script explicitly chooses the CPU
platform, including hydrogen preparation; it does not consume an extra GPU.

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
successful checkpoints. Boltz-2 uses `fold_boltz2.py` with its own result
directory and explicit `use_msa=False`; no MSA server is contacted on compute
nodes.

CPU jobs are submitted using the CPU template:

```bash
sbatch protease_design/scripts/cpu.slurm \
  protease_design/scripts/analyze_structures.py
sbatch protease_design/scripts/cpu.slurm \
  protease_design/scripts/refine_geometry.py \
  data/corehpc/protease_design/inputs/candidates.json --only CDAD_WT_GS3
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
