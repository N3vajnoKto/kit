#!/bin/sh

# Determine the absolute path to the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check if the original configuration files exist next to the script
if [ ! -f "$SCRIPT_DIR/.clang-format" ] || [ ! -f "$SCRIPT_DIR/.clang-tidy" ]; then
    echo "Error: .clang-format or .clang-tidy not found in the script directory ($SCRIPT_DIR)."
    exit 1
fi

echo "Creating symlinks in the current directory: $PWD"

# Create symlink for .clang-format
if [ -e ".clang-format" ] || [ -L ".clang-format" ]; then
    echo "⚠️  File or symlink .clang-format already exists in this directory. Skipping."
else
    ln -s "$SCRIPT_DIR/.clang-format" .clang-format
    echo "✅ Symlink for .clang-format successfully created."
fi

# Create symlink for .clang-tidy
if [ -e ".clang-tidy" ] || [ -L ".clang-tidy" ]; then
    echo "⚠️  File or symlink .clang-tidy already exists in this directory. Skipping."
else
    ln -s "$SCRIPT_DIR/.clang-tidy" .clang-tidy
    echo "✅ Symlink for .clang-tidy successfully created."
fi
