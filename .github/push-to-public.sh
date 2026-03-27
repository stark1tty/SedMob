#!/bin/bash
# Push to public repo (stark1tty/SedMob) respecting .gitignore
# Use this instead of pushing directly to origin

set -e

echo "📤 Pushing to public repo (respecting .gitignore)..."

# Create a temporary branch without ignored files
git checkout -b temp-public-push

# Remove ignored files from the index (but not from working directory)
git rm -r --cached .archives .claude .kiro .pwlw-sedmob .venv .pytest_cache .github .vscode 2>/dev/null || true

# Commit the cleaned state
git commit -m "temp: Clean for public push" --allow-empty

# Push to origin (public)
git push origin temp-public-push:master --force

# Return to master and cleanup
git checkout master
git branch -D temp-public-push

echo "✅ Public repo updated successfully!"
echo "💾 Private repo (backup) still has all your files"
