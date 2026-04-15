#!/bin/bash
# Setup script for publishing Skillboard to GitHub and PyPI

set -e

echo "🚀 Skillboard Release Setup"
echo ""

# Check for required tools
echo "Checking prerequisites..."
command -v git >/dev/null 2>&1 || { echo "❌ git is required but not installed."; exit 1; }
command -v python >/dev/null 2>&1 || { echo "❌ python is required but not installed."; exit 1; }
command -v pipx >/dev/null 2>&1 || { echo "❌ pipx is required but not installed. Run: pip install pipx"; exit 1; }

echo "✓ All prerequisites met"
echo ""

# Get GitHub username
echo "Enter your GitHub username:"
read -r GITHUB_USER

if [ -z "$GITHUB_USER" ]; then
    echo "❌ GitHub username is required"
    exit 1
fi

echo ""
echo "Setting up project for GitHub user: $GITHUB_USER"
echo ""

# Update URLs in pyproject.toml
echo "📝 Updating project URLs..."
sed -i "s|user/skillboard|$GITHUB_USER/skillboard|g" pyproject.toml
sed -i "s|user/skillboard|$GITHUB_USER/skillboard|g" README.md
sed -i "s|user/skillboard|$GITHUB_USER/skillboard|g" skillboard/__init__.py
echo "✓ URLs updated"
echo ""

# Commit changes
echo "📝 Committing URL updates..."
git add -A
git commit -m "chore: update project URLs for $GITHUB_USER" || echo "No changes to commit"
echo "✓ Changes committed"
echo ""

# Build package
echo "📦 Building package..."
# Create temp venv for building
python -m venv .venv-build
source .venv-build/bin/activate
pip install build twine -q
python -m build
deactivate
rm -rf .venv-build
echo "✓ Package built"
echo ""

# Check package
echo "🔍 Checking package..."
pipx run twine check dist/*
echo "✓ Package check passed"
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo ""
echo "1. Create GitHub repository:"
echo "   Visit: https://github.com/new"
echo "   Repository name: skillboard"
echo "   ☑️ Initialize with README (optional)"
echo ""
echo "2. Push code to GitHub:"
echo "   git remote add origin https://github.com/$GITHUB_USER/skillboard.git"
echo "   git push -u origin main"
echo "   git push origin v0.1.0"
echo ""
echo "3. Create PyPI account:"
echo "   Visit: https://pypi.org/account/register/"
echo ""
echo "4. Create PyPI API token:"
echo "   Visit: https://pypi.org/manage/account/token/"
echo "   Create token with scope: 'Entire account (all projects)'"
echo ""
echo "5. Add PyPI token to GitHub secrets:"
echo "   Visit: https://github.com/$GITHUB_USER/skillboard/settings/secrets/actions"
echo "   New repository secret:"
echo "   Name: PYPI_API_TOKEN"
echo "   Value: <your-pypi-token>"
echo ""
echo "6. Publish manually (optional):"
echo "   pipx run twine upload dist/*"
echo "   Username: __token__"
echo "   Password: <your-pypi-token>"
echo ""
echo "7. Or push a new tag to trigger automatic publishing:"
echo "   git tag v0.1.1"
echo "   git push origin v0.1.1"
echo ""
echo "═══════════════════════════════════════════════════════════"
