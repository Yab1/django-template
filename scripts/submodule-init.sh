#!/bin/bash
set -e

if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -n "$GIT_USERNAME" ] && [ -n "$GIT_TOKEN" ]; then
    GIT_USERNAME_CLEAN=$(echo "$GIT_USERNAME" | sed 's/^"//;s/"$//')
    GIT_TOKEN_CLEAN=$(echo "$GIT_TOKEN" | sed 's/^"//;s/"$//')
    echo "Configuring git to use HTTPS with credentials..."
    # Rewrite SSH URLs to HTTPS with credentials
    git config --local url."https://${GIT_USERNAME_CLEAN}:${GIT_TOKEN_CLEAN}@github.com/".insteadOf "git@github.com:"
    # Also rewrite plain HTTPS URLs to include credentials
    git config --local url."https://${GIT_USERNAME_CLEAN}:${GIT_TOKEN_CLEAN}@github.com/".insteadOf "https://github.com/"
else
    echo "No GIT_USERNAME/GIT_TOKEN found in .env, using default git authentication"
fi

echo "Reading submodules from .gitmodules..."
SUBMODULE_PATHS=$(git config --file=.gitmodules --get-regexp path | awk '{print $2}' || true)

if [ -z "$SUBMODULE_PATHS" ]; then
    echo "No submodules found in .gitmodules"
    exit 0
fi

# Clear any existing submodule configs to avoid cached SSH URLs
echo "Clearing cached submodule configs..."
for SUBMODULE_PATH in $SUBMODULE_PATHS; do
    git config --local --unset "submodule.${SUBMODULE_PATH}.url" 2>/dev/null || true
done

# Sync submodule URLs (this reads from .gitmodules)
echo "Syncing submodule URLs..."
git submodule sync --recursive

# Force set URLs from .gitmodules to ensure HTTPS URLs are used (not cached SSH URLs)
echo "Setting submodule URLs from .gitmodules..."
for SUBMODULE_PATH in $SUBMODULE_PATHS; do
    # Get the submodule section name (the quoted part in [submodule "name"])
    SUBMODULE_SECTION=$(git config --file=.gitmodules --get-regexp "submodule\..*\.path" | \
                        grep " ${SUBMODULE_PATH}$" | head -1 | \
                        sed 's/^submodule\.\(.*\)\.path.*/\1/' || echo "")
    
    # If section extraction failed, try using path directly
    if [ -z "$SUBMODULE_SECTION" ]; then
        SUBMODULE_SECTION="$SUBMODULE_PATH"
    fi
    
    # Try with section name first, then with path as fallback
    SUBMODULE_URL=$(git config --file=.gitmodules --get "submodule.\"${SUBMODULE_SECTION}\".url" || \
                    git config --file=.gitmodules --get "submodule.${SUBMODULE_SECTION}.url" || \
                    git config --file=.gitmodules --get "submodule.${SUBMODULE_PATH}.url" || \
                    git config --file=.gitmodules --get "submodule.\"${SUBMODULE_PATH}\".url" || echo "")
    
    if [ -n "$SUBMODULE_URL" ]; then
        # Convert any SSH URLs to HTTPS (since all submodules use HTTPS)
        if [[ "$SUBMODULE_URL" == git@github.com:* ]]; then
            REPO_PATH=$(echo "$SUBMODULE_URL" | sed 's|git@github.com:||' | sed 's|\.git$||')
            SUBMODULE_URL="https://github.com/${REPO_PATH}.git"
        fi
        
        # If we have credentials, inject them into the URL
        CONFIG_URL="$SUBMODULE_URL"
        if [ -n "$GIT_USERNAME_CLEAN" ] && [ -n "$GIT_TOKEN_CLEAN" ]; then
            if [[ "$SUBMODULE_URL" == https://github.com/* ]]; then
                CONFIG_URL=$(echo "$SUBMODULE_URL" | sed "s|https://github.com/|https://${GIT_USERNAME_CLEAN}:${GIT_TOKEN_CLEAN}@github.com/|")
            fi
        fi
        
        echo "  Setting URL for $SUBMODULE_PATH to $SUBMODULE_URL"
        git config --local "submodule.${SUBMODULE_PATH}.url" "$CONFIG_URL"
    fi
done

echo "Initializing all submodules..."
git submodule init

echo ""
echo "Cloning all submodules recursively..."

FAILED_SUBMODULES=()

for SUBMODULE_PATH in $SUBMODULE_PATHS; do
    # Extract submodule name from .gitmodules section
    # Get the section name (the quoted part in [submodule "name"])
    SUBMODULE_SECTION=$(git config --file=.gitmodules --get-regexp "submodule\..*\.path" | \
                        grep " ${SUBMODULE_PATH}$" | head -1 | \
                        sed 's/^submodule\.\(.*\)\.path.*/\1/' || echo "")
    
    # Use section name as display name, fallback to basename of path
    if [ -n "$SUBMODULE_SECTION" ]; then
        SUBMODULE_NAME="$SUBMODULE_SECTION"
    else
        SUBMODULE_NAME=$(basename "$SUBMODULE_PATH")
    fi
    
    if [ -d "$SUBMODULE_PATH/.git" ] || [ -f "$SUBMODULE_PATH/.git" ]; then
        echo "  ✓ $SUBMODULE_NAME already exists"
        continue
    fi
    
    # Get URL from .gitmodules using section name (preferred) or path (fallback)
    if [ -n "$SUBMODULE_SECTION" ]; then
        SUBMODULE_URL=$(git config --file=.gitmodules --get "submodule.\"${SUBMODULE_SECTION}\".url" || \
                        git config --file=.gitmodules --get "submodule.${SUBMODULE_SECTION}.url" || echo "")
    fi
    
    # Fallback to path-based lookup if section-based failed
    if [ -z "$SUBMODULE_URL" ]; then
        SUBMODULE_URL=$(git config --file=.gitmodules --get "submodule.${SUBMODULE_PATH}.url" || \
                        git config --file=.gitmodules --get "submodule.\"${SUBMODULE_PATH}\".url" || echo "")
    fi
    
    if [ -z "$SUBMODULE_URL" ]; then
        echo "  ✗ No URL found for $SUBMODULE_NAME in .gitmodules"
        FAILED_SUBMODULES+=("$SUBMODULE_NAME")
        continue
    fi
    
    # Convert SSH to HTTPS if needed (all submodules should use HTTPS)
    if [[ "$SUBMODULE_URL" == git@github.com:* ]]; then
        REPO_PATH=$(echo "$SUBMODULE_URL" | sed 's|git@github.com:||' | sed 's|\.git$||')
        SUBMODULE_URL="https://github.com/${REPO_PATH}.git"
    fi
    
    # Force set URL in git config (overwrite any cached value)
    # If we have credentials, use URL with credentials for git operations
    # Re-check credentials in case they weren't set earlier
    if [ -z "$GIT_USERNAME_CLEAN" ] || [ -z "$GIT_TOKEN_CLEAN" ]; then
        if [ -n "$GIT_USERNAME" ] && [ -n "$GIT_TOKEN" ]; then
            GIT_USERNAME_CLEAN=$(echo "$GIT_USERNAME" | sed 's/^"//;s/"$//')
            GIT_TOKEN_CLEAN=$(echo "$GIT_TOKEN" | sed 's/^"//;s/"$//')
        fi
    fi
    
    CONFIG_URL="$SUBMODULE_URL"
    if [ -n "$GIT_USERNAME_CLEAN" ] && [ -n "$GIT_TOKEN_CLEAN" ]; then
        if [[ "$SUBMODULE_URL" == https://github.com/* ]]; then
            CONFIG_URL=$(echo "$SUBMODULE_URL" | sed "s|https://github.com/|https://${GIT_USERNAME_CLEAN}:${GIT_TOKEN_CLEAN}@github.com/|")
        fi
    fi
    git config --local "submodule.${SUBMODULE_PATH}.url" "$CONFIG_URL"
    
    # Verify the URL was set correctly
    VERIFIED_URL=$(git config --get "submodule.${SUBMODULE_PATH}.url" || echo "")
    if [ "$VERIFIED_URL" != "$CONFIG_URL" ]; then
        echo "  ⚠ URL mismatch! Expected: $CONFIG_URL, Got: $VERIFIED_URL"
        echo "  Forcing URL again..."
        git config --local "submodule.${SUBMODULE_PATH}.url" "$CONFIG_URL"
    fi
    
    # Try git submodule update first (works if submodule is already registered)
    if git submodule update --init --recursive "$SUBMODULE_PATH" 2>/dev/null; then
        echo "  ✓ Cloned $SUBMODULE_NAME"
    else
        # If update fails, try direct clone (for clean installs)
        PARENT_DIR=$(dirname "$SUBMODULE_PATH")
        [ "$PARENT_DIR" != "." ] && mkdir -p "$PARENT_DIR"
        
        # If we have credentials, inject them into the URL for direct clone
        CLONE_URL="$SUBMODULE_URL"
        # Re-check credentials in case they weren't set earlier (for robustness)
        if [ -z "$GIT_USERNAME_CLEAN" ] || [ -z "$GIT_TOKEN_CLEAN" ]; then
            if [ -n "$GIT_USERNAME" ] && [ -n "$GIT_TOKEN" ]; then
                GIT_USERNAME_CLEAN=$(echo "$GIT_USERNAME" | sed 's/^"//;s/"$//')
                GIT_TOKEN_CLEAN=$(echo "$GIT_TOKEN" | sed 's/^"//;s/"$//')
            fi
        fi
        
        if [ -n "$GIT_USERNAME_CLEAN" ] && [ -n "$GIT_TOKEN_CLEAN" ]; then
            # Inject credentials into HTTPS URLs
            if [[ "$SUBMODULE_URL" == https://github.com/* ]]; then
                CLONE_URL=$(echo "$SUBMODULE_URL" | sed "s|https://github.com/|https://${GIT_USERNAME_CLEAN}:${GIT_TOKEN_CLEAN}@github.com/|")
            fi
        fi
        
        echo "  Attempting direct clone for $SUBMODULE_NAME..."
        # Try clone with error output to a temp file for debugging
        CLONE_ERROR=$(mktemp)
        if git clone --recursive "$CLONE_URL" "$SUBMODULE_PATH" 2>"$CLONE_ERROR"; then
            echo "  ✓ Cloned $SUBMODULE_NAME directly"
            rm -f "$CLONE_ERROR"
            # After direct clone, ensure it's properly registered (use original URL without credentials)
            git config --local "submodule.${SUBMODULE_PATH}.url" "$SUBMODULE_URL"
            git config --local "submodule.${SUBMODULE_PATH}.path" "$SUBMODULE_PATH"
        else
            echo "  ✗ Failed to clone $SUBMODULE_NAME"
            # Show first line of error for debugging (without exposing full token)
            ERROR_MSG=$(head -1 "$CLONE_ERROR" 2>/dev/null || echo "Unknown error")
            echo "     Error: $ERROR_MSG" | sed "s/${GIT_TOKEN_CLEAN}/***/g"
            rm -f "$CLONE_ERROR"
            FAILED_SUBMODULES+=("$SUBMODULE_NAME")
        fi
    fi
done

# Exit early if any submodules failed to clone
if [ ${#FAILED_SUBMODULES[@]} -gt 0 ]; then
    echo ""
    echo "ERROR: The following submodules failed to clone:"
    printf '  - %s\n' "${FAILED_SUBMODULES[@]}"
    exit 1
fi

echo ""
echo "Updating submodules to latest commits..."

for SUBMODULE_PATH in $SUBMODULE_PATHS; do
    if [ ! -d "$SUBMODULE_PATH/.git" ] && [ ! -f "$SUBMODULE_PATH/.git" ]; then
        continue
    fi
    
    # Extract submodule name and section for branch lookup
    SUBMODULE_SECTION=$(git config --file=.gitmodules --get-regexp "submodule\..*\.path" | \
                        grep " ${SUBMODULE_PATH}$" | head -1 | \
                        sed 's/^submodule\.\(.*\)\.path.*/\1/' || echo "")
    
    if [ -n "$SUBMODULE_SECTION" ]; then
        SUBMODULE_NAME="$SUBMODULE_SECTION"
    else
        SUBMODULE_NAME=$(basename "$SUBMODULE_PATH")
    fi
    
    # Get branch using section name (preferred) or path (fallback)
    if [ -n "$SUBMODULE_SECTION" ]; then
        SUBMODULE_BRANCH=$(git config --file=.gitmodules --get "submodule.\"${SUBMODULE_SECTION}\".branch" || \
                          git config --file=.gitmodules --get "submodule.${SUBMODULE_SECTION}.branch" || echo "main")
    else
        SUBMODULE_BRANCH=$(git config --file=.gitmodules --get "submodule.${SUBMODULE_PATH}.branch" || echo "main")
    fi
    
    (
        cd "$SUBMODULE_PATH"
        if ! git fetch origin 2>/dev/null; then
            echo "  ⚠ Failed to fetch $SUBMODULE_NAME"
            exit 0
        fi
        
        if git checkout "$SUBMODULE_BRANCH" 2>/dev/null || git checkout -b "$SUBMODULE_BRANCH" "origin/$SUBMODULE_BRANCH" 2>/dev/null; then
            git pull origin "$SUBMODULE_BRANCH" 2>/dev/null || true
        else
            echo "  ⚠ Failed to checkout branch $SUBMODULE_BRANCH for $SUBMODULE_NAME"
        fi
    )
done

echo ""
echo "=== Submodule Status ==="
git submodule status --recursive

MISSING=$(git submodule status --recursive | grep -c "^-" || true)
if [ "$MISSING" -gt 0 ]; then
    echo ""
    echo "WARNING: $MISSING submodule(s) failed to initialize!"
    echo ""
    echo "Failed submodules:"
    git submodule status --recursive | grep "^-" | awk '{print "  - " $2}'
    exit 1
fi

echo ""
echo "✔ All submodules initialized successfully"
