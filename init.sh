#!/bin/bash

# Determine the absolute path to the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SOURCE_HOOKS_DIR="$SCRIPT_DIR/git-hooks"
GIT_HOOKS_DIR=".git/hooks"

echo "========================================="
echo "⚙️  Initializing project environments..."
echo "========================================="

# -----------------------------------------------------------------------------
# STEP 1: Creating symlinks for Clang-Format and Clang-Tidy
# -----------------------------------------------------------------------------
if [ ! -f "$SCRIPT_DIR/.clang-format" ] || [ ! -f "$SCRIPT_DIR/.clang-tidy" ]; then
    echo "❌ Error: .clang-format or .clang-tidy not found in the script directory."
    exit 1
fi

echo "🔗 Setting up configuration symlinks in: $PWD"

for config_file in ".clang-format" ".clang-tidy"; do
    if [ -e "$config_file" ] || [ -L "$config_file" ]; then
        echo "⚠️  $config_file already exists in the destination. Skipping symlink."
    else
        ln -s "$SCRIPT_DIR/$config_file" "$config_file"
        echo "✅ Symlink for $config_file successfully created."
    fi
done

# -----------------------------------------------------------------------------
# STEP 2: Checking existing Git hooks (Warning step)
# -----------------------------------------------------------------------------
if [ ! -d "$GIT_HOOKS_DIR" ]; then
    echo "❌ Error: .git/hooks directory not found. Are you in the root of a Git repository?"
    exit 1
fi

echo -e "\n🔍 Checking existing Git hooks..."
EXISTING_HOOKS=$(find "$GIT_HOOKS_DIR" -maxdepth 1 -type f ! -name "*.sample")

if [ -n "$EXISTING_HOOKS" ]; then
    echo "⚠️  Warning: The following custom Git hooks are already present in your project:"
    while read -r hook; do
        echo "   - $(basename "$hook")"
    done <<< "$EXISTING_HOOKS"
    echo "👉 Note: These hooks were NOT modified or overwritten."
else
    echo "ℹ️  No active custom hooks found in .git/hooks/."
fi

# -----------------------------------------------------------------------------
# STEP 3: Deploying hooks from the git-hooks/ folder
# -----------------------------------------------------------------------------
echo -e "\n🚀 Deploying project-specific Git hooks from: git-hooks/"

if [ ! -d "$SOURCE_HOOKS_DIR" ]; then
    echo "⚠️  Skipping hooks installation: Folder '$SOURCE_HOOKS_DIR' does not exist."
else
    # Find all files inside the source git-hooks directory
    FOUND_HOOKS=$(find "$SOURCE_HOOKS_DIR" -maxdepth 1 -type f)
    
    if [ -z "$FOUND_HOOKS" ]; then
        echo "ℹ️  No files found inside the '$SOURCE_HOOKS_DIR' directory to install."
    else
        while read -r src_hook_path; do
            HOOK_NAME=$(basename "$src_hook_path")
            DEST_HOOK="$GIT_HOOKS_DIR/$HOOK_NAME"
            
            # Check if this hook already exists in the destination
            if [ -e "$DEST_HOOK" ] || [ -L "$DEST_HOOK" ]; then
                echo "⚠️  The hook '$HOOK_NAME' already exists in .git/hooks/. Will NOT overwrite."
            else
                # Copy the hook into .git/hooks/ and make it executable
                cp "$src_hook_path" "$DEST_HOOK"
                chmod +x "$DEST_HOOK"
                echo "✅ Installed '$HOOK_NAME' to .git/hooks/ and made it executable."
            fi
        done <<< "$FOUND_HOOKS"
    fi
fi

echo -e "\n========================================="
echo "🎉 Done! Project setup Completed Successfully."
echo "========================================="
