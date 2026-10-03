#!/bin/bash
# Source from the project mirror before setup and in every SLURM job.
export PROTO_HOME="$PWD/data/corehpc/proto"
export PROTO_MODEL_CACHE="$PROTO_HOME/proto_model_cache"
export PROTO_DATABASES_DIR="$PROTO_MODEL_CACHE/databases"
export XDG_CACHE_HOME="$PWD/data/corehpc/cache"
export PIP_CACHE_DIR="$PROTO_HOME/pip_cache"
export UV_CACHE_DIR="$PROTO_HOME/uv_cache"
export HF_HOME="$PROTO_MODEL_CACHE/huggingface"
export TORCH_HOME="$PROTO_MODEL_CACHE/torch"
export MPLCONFIGDIR="$XDG_CACHE_HOME/matplotlib"
export APPTAINER_CACHEDIR="$PWD/data/corehpc/containers/cache"
export APPTAINER_TMPDIR="$PWD/data/corehpc/containers/tmp"
export TMPDIR="$PWD/data/corehpc/tmp/${SLURM_JOB_ID:-setup}"
export PROTO_ENV_LOG_DIR="$PWD/logs/protease_env"
export PROTO_ENV_VERBOSE=1
mkdir -p "$PROTO_HOME" "$PROTO_MODEL_CACHE" "$PROTO_DATABASES_DIR" \
  "$XDG_CACHE_HOME" "$PIP_CACHE_DIR" "$UV_CACHE_DIR" "$HF_HOME" \
  "$TORCH_HOME" "$TMPDIR" "$PROTO_ENV_LOG_DIR" "$MPLCONFIGDIR" \
  "$APPTAINER_CACHEDIR" "$APPTAINER_TMPDIR" \
  data/corehpc/protease_design/results logs
