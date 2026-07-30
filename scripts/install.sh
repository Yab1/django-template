#!/bin/bash

# Load environment variables from .env file
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs) 2>/dev/null || true
fi

# Ensure uv is in PATH
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

# Check if uv exists
if [ -f "$HOME/.local/bin/uv" ]; then
    echo "uv found at $HOME/.local/bin/uv"
elif [ -f "$HOME/.cargo/bin/uv" ]; then
    echo "uv found at $HOME/.cargo/bin/uv"
elif ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

# Configure git credentials for private repositories
if [ -n "$GIT_USERNAME" ] && [ -n "$GIT_TOKEN" ]; then
    GIT_USERNAME_CLEAN=$(echo "$GIT_USERNAME" | sed 's/^"//;s/"$//')
    GIT_TOKEN_CLEAN=$(echo "$GIT_TOKEN" | sed 's/^"//;s/"$//')
    git config --global url."https://${GIT_USERNAME_CLEAN}:${GIT_TOKEN_CLEAN}@github.com/".insteadOf "https://github.com/" || true
fi

# Generate lock file if needed
if [ ! -f "uv.lock" ]; then
    echo "Generating uv.lock file..."
    uv lock
fi

# Sync dependencies
echo "Syncing dependencies with uv..."
uv sync --all-extras
