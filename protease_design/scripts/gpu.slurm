#!/bin/bash
#SBATCH --job-name=protease-gpu
#SBATCH --comment=protease_design
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=00:30:00
#SBATCH --chdir=/mnt/scratch/group/CX500059_DS1/blonnquist/proto-tools-moonshot
#SBATCH --output=logs/protease_gpu_%j.out
#SBATCH --error=logs/protease_gpu_%j.err
set -euo pipefail
module purge
module load CBI
module load nvidia-hpc
module load nvhpc/26.5
source protease_design/scripts/corehpc_env.sh
export OMP_NUM_THREADS="$SLURM_CPUS_PER_TASK"
export OPENBLAS_NUM_THREADS="$SLURM_CPUS_PER_TASK"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
git rev-parse HEAD
date -u
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv
srun .venv/bin/python "$@"
