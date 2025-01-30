#!/usr/bin/env bash

set -euo pipefail

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to display usage information
usage() {
    echo "Usage: $0 <commit-sha>"
    echo "Example: $0 abcdef1234567890abcdef1234567890abcdef12"
    exit 1
}

# Function to print error messages
error_echo() {
    echo "Error: $1"
}

# Check if a commit SHA is provided
if [ -z "${1:-}" ]; then
    error_echo "No commit SHA provided."
    usage
fi

COMMIT_SHA="$1"

# Validate commit SHA format
if ! [[ "$COMMIT_SHA" =~ ^[a-fA-F0-9]{40}$ ]]; then
    error_echo "Invalid commit SHA format."
    usage
fi

# Ensure required commands are available
required_commands=("git" "cmake" "ninja" "clang2py")
for cmd in "${required_commands[@]}"; do
    if ! command -v "$cmd" &> /dev/null; then
        error_echo "$cmd is not installed."
        exit 1
    fi
done

# Pull the subtree with the provided commit SHA
echo "Pulling subtree with commit SHA: $COMMIT_SHA"
git subtree pull --prefix=depend/bitcoin https://github.com/bitcoin/bitcoin "$COMMIT_SHA" --squash

echo "Subtree pulled successfully."

cmake --B build
cmake --build build -j

# Install and capture library path
INSTALL_OUTPUT=$(sudo cmake --install build 2>&1)
LIB_PATH=$(echo "$INSTALL_OUTPUT" | grep -Eo '/[^ ]+\.(so|dylib|dll)') || true

NM_OPTION=""
if [[ "${OSTYPE}" == "darwin"* ]]; then
    NM_OPTION="--nm $SCRIPT_DIR/nm_patch.py"
fi

if [ -z "$LIB_PATH" ]; then
    echo "Error: Library path not found."
    exit 1
fi

OUTPUT_FILE="bindings.py.new"

if [ -f "$OUTPUT_FILE" ]; then
    echo "Warning: $OUTPUT_FILE already exists and will be overwritten."
fi

clang2py "$SCRIPT_DIR/../depend/bitcoin/src/kernel/bitcoinkernel.h" -l "$LIB_PATH" $NM_OPTION > "$OUTPUT_FILE"

echo "Bindings generated successfully at $OUTPUT_FILE."
