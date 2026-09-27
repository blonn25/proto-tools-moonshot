#!/bin/bash
set -euo pipefail
source standalone_helpers.sh

proto_install_cuda_toolkit
proto_install_jax

echo "Mock JAX tool setup complete"
