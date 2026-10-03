#!/bin/bash
#SBATCH --job-name=protease-cpu
#SBATCH --comment=protease_design
#SBATCH --partition=cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --chdir=/mnt/scratch/group/CX500059_DS1/blonnquist/proto-tools-moonshot
#SBATCH --output=logs/protease_cpu_%j.out
#SBATCH --error=logs/protease_cpu_%j.err
set -euo pipefail
module purge
module load CBI
source protease_design/scripts/corehpc_env.sh
export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK"
export OPENBLAS_NUM_THREADS="$SLURM_CPUS_PER_TASK"
git rev-parse HEAD
date -u
srun --ntasks=1 .venv/bin/python "$@"
