#!/bin/bash

# Enforce a robust, universal .gitignore pattern matrix if none exists
if [ ! -f ".gitignore" ]; then
    echo "Creating generic .gitignore framework..."
    cat <<EOT > .gitignore
# Virtual Environments
*env/
*ENV/
.venv/
venv/

# Python Compilation Artifacts
__pycache__/
*.pyc
*.pyo
*.pyd

# Application Configuration & System Level
.vscode/
.idea/
.DS_Store
Thumbs.db
EOT
fi

# =====================================================================
# CORE SAFEGUARD: PRE-COMMIT FILE SIZE HOOK (50MB CONSTRAINT)
# =====================================================================
check_file_sizes() {
    # 50MB translated directly to bytes (50 * 1024 * 1024)
    local max_bytes=52428800
    local standard_block=""

    # Read names of all staged files about to be committed
    staged_files=$(git diff --cached --name-only)

    for file in $staged_files; do
        if [ -f "$file" ]; then
            # Cross-platform safe byte count retrieval
            local file_bytes=$(wc -c < "$file")
            if [ "$file_bytes" -gt "$max_bytes" ]; then
                local size_mb=$((file_bytes / 1024 / 1024))
                standard_block="${standard_block}\n🚨 $file ($size_mb MB)"
            fi
        fi
    done

    if [ ! -z "$standard_block" ]; then
        echo "========================================================="
        echo "🛑 DEPLOYMENT ABORTED: LARGE FILES DETECTED"
        echo "========================================================="
        echo -e "$standard_block"
        echo ""
        echo "Reason: GitHub flags warnings at 50MB and rejects pushes entirely"
        echo "        at 100MB. Please untrack or remove these assets."
        echo "========================================================="
        exit 1
    fi
}

# Detect whether the local tracking tree has been initialized
if [ ! -d ".git" ]; then
    echo "========================================================="
    echo "       INITIAL REPOSITORY UPSTREAM SET-UP INTERFACE"
    echo "========================================================="
    echo ""
    read -p "Enter target remote GitHub repository URL: " repo_url

    if [ -z "$repo_url" ]; then
        echo "Error: Repository URL cannot be empty."
        exit 1
    fi

    echo "Processing local repository initialization..."
    git init
    git add .
    
    # Run size check immediately after staging files
    check_file_sizes
    
    git commit -m "Initial commit: Production deployment architecture blueprint"
    git branch -M main
    
    echo "Establishing connection link with remote repository..."
    git remote add origin "$repo_url"
    
    echo "Pushing codebase records up to GitHub main branch..."
    git push -u origin main
    
    echo "========================================================="
    echo "Success: Workspace initialization completed and synced to GitHub."
    echo "========================================================="
else
    echo "========================================================="
    echo "             INCREMENTAL DELTA DEPLOYMENT INTERFACE"
    echo "========================================================="
    echo ""
    
    echo "Staging modifications..."
    git add .
    
    # Run size check before allowing the git commit step to fire
    check_file_sizes
    
    # FIX: Check if there are actually changes BEFORE bothering you for a message
    if git diff --cached --quiet; then
        echo "Info: No new changes detected in your workspace. Sync bypassed."
    else
        if [ -n "$1" ]; then
            commit_msg="$1"
        else
            read -p "Enter commit classification message [Press Enter for default]: " commit_msg

            if [ -z "$commit_msg" ]; then
                commit_msg="Refine codebase configurations and processing core parameters"
            fi
        fi

        git commit -m "$commit_msg"
        echo "Deploying delta vectors to GitHub tracking tree..."
        git push
        echo "========================================================="
        echo "Success: Cloud synchronization execution completed."
        echo "========================================================="
    fi
fi