#!/bin/bash

# Load environment variables from .env file
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs) 2>/dev/null || true
fi

# Ensure uv is in PATH and install if missing
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

# Generate lock file if needed
if [ ! -f "uv.lock" ]; then
    echo "Generating uv.lock file..."
    uv lock
fi

# Sync dependencies
echo "Syncing dependencies with uv..."
uv sync --all-extras
