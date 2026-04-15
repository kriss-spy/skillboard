# Publishing Skillboard

This guide walks you through publishing Skillboard to GitHub and PyPI.

## Quick Start

Run the setup script:

```bash
./setup-release.sh
```

Or follow the manual steps below.

---

## Manual Setup

### 1. Update Project URLs

Replace `user/skillboard` with your GitHub username in these files:

**pyproject.toml:**
```toml
[project.urls]
Homepage = "https://github.com/YOUR_USERNAME/skillboard"
Repository = "https://github.com/YOUR_USERNAME/skillboard"
Issues = "https://github.com/YOUR_USERNAME/skillboard/issues"
```

**README.md:**
```markdown
### From Source

```bash
git clone https://github.com/YOUR_USERNAME/skillboard.git
cd skillboard
pip install -e .
```
```

**skillboard/__init__.py:**
```python
__url__ = "https://github.com/YOUR_USERNAME/skillboard"
```

Commit these changes:
```bash
git add -A
git commit -m "chore: update project URLs"
```

---

### 2. Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `skillboard`
3. Description: `A lightweight skill management utility for AI coding agents`
4. Make it Public
5. ☑️ Add a README file (optional)
6. ☑️ Add .gitignore: Python (optional)
7. ☑️ Choose a license: MIT (optional)
8. Click **Create repository**

---

### 3. Push Code to GitHub

```bash
# Add remote
git remote add origin https://github.com/YOUR_USERNAME/skillboard.git

# Push code
git push -u origin main

# Push tags
git push origin v0.1.0
```

---

### 4. Create PyPI Account

1. Go to https://pypi.org/account/register/
2. Fill in your details
3. Verify your email address

---

### 5. Create PyPI API Token

1. Go to https://pypi.org/manage/account/token/
2. Click **Add API token**
3. Token name: `skillboard-release`
4. Scope: `Entire account (all projects)`
5. Click **Create token**
6. **Copy the token immediately** (you won't see it again!)

---

### 6. Add PyPI Token to GitHub Secrets

This allows GitHub Actions to publish automatically:

1. Go to `https://github.com/YOUR_USERNAME/skillboard/settings/secrets/actions`
2. Click **New repository secret**
3. Name: `PYPI_API_TOKEN`
4. Value: Paste your PyPI token from step 5
5. Click **Add secret**

---

### 7. Publish to PyPI

#### Option A: Automatic (via GitHub Actions)

Push a new version tag to trigger automatic publishing:

```bash
# Update version in skillboard/__init__.py and pyproject.toml
git add -A
git commit -m "chore: bump version to 0.1.1"

# Create new tag
git tag v0.1.1

# Push
git push origin main
git push origin v0.1.1
```

The CI workflow will automatically:
- Run tests on Python 3.9-3.13
- Check code formatting
- Build the package
- Publish to PyPI

#### Option B: Manual

```bash
# Install build tools
pip install build twine

# Build package
python -m build

# Check package
twine check dist/*

# Upload to PyPI
twine upload dist/*

# Username: __token__
# Password: <your-pypi-api-token>
```

---

### 8. Verify Installation

Once published, anyone can install it:

```bash
pipx install skillboard
# or
pip install skillboard
```

Test it:
```bash
skillboard --version
skillboard list
```

---

## Release Checklist

Before each release:

- [ ] Update version in `skillboard/__init__.py`
- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG.md (if you have one)
- [ ] Run tests: `pytest`
- [ ] Check formatting: `black --check skillboard/`
- [ ] Check linting: `ruff check skillboard/`
- [ ] Commit all changes
- [ ] Create git tag: `git tag vX.Y.Z`
- [ ] Push: `git push origin main && git push origin vX.Y.Z`
- [ ] Verify CI passes on GitHub
- [ ] Verify package appears on PyPI: https://pypi.org/project/skillboard/

---

## Troubleshooting

### Git push fails

```bash
# If you get "rejected" errors
git pull origin main --rebase
git push origin main
```

### PyPI upload fails

- Ensure your token is correct
- Check that the version number is unique (PyPI doesn't allow overwriting)
- Check package with `twine check dist/*`

### GitHub Actions fails

- Check the Actions tab: `https://github.com/YOUR_USERNAME/skillboard/actions`
- Ensure `PYPI_API_TOKEN` secret is set correctly
- Check that tests pass locally: `pytest`

---

## Badges

Add these badges to your README after publishing:

```markdown
[![PyPI version](https://badge.fury.io/py/skillboard.svg)](https://badge.fury.io/py/skillboard)
[![CI](https://github.com/YOUR_USERNAME/skillboard/workflows/CI/badge.svg)](https://github.com/YOUR_USERNAME/skillboard/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
```

---

## Congratulations! 🎉

Your package is now published and available to the Python community!
