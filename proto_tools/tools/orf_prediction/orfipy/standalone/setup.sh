#!/bin/bash
set -euo pipefail

echo "Setting up Orfipy standalone environment..."

echo "Installing Python dependencies..."
uv pip install -r requirements.txt

echo "Orfipy setup complete!"
