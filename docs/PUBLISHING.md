# Publishing GenXAI to PyPI

This guide explains how to publish GenXAI to the Python Package Index (PyPI) so users can install it with `pip install genxai`.

## Prerequisites

1. **PyPI Account**
   - Create account at https://pypi.org/account/register/
   - Verify your email address
   - Enable 2FA (recommended)

2. **TestPyPI Account** (for testing)
   - Create account at https://test.pypi.org/account/register/
   - This is a separate instance for testing

3. **API Tokens**
   - Generate API token at https://pypi.org/manage/account/token/
   - Generate TestPyPI token at https://test.pypi.org/manage/account/token/
   - Store tokens securely (you'll need them for publishing)

## Setup

### 1. Install Build Tools

```bash
pip install --upgrade build twine
```

### 2. Configure PyPI Credentials

Create `~/.pypirc` file:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PYPI_API_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TESTPYPI_API_TOKEN_HERE
```

**Security Note**: Keep this file private! Add to `.gitignore`.

## Publishing Process

## OSS vs Enterprise Packaging

PyPI releases are **OSS-only**. The packaging config in `pyproject.toml` includes only
`genxai*` and explicitly excludes `tests*`, `docs*`, `examples*`, `studio*`, and anything
under `enterprise/`. That means a `pip install genxai` publishes/installs the open-source
core only.

To verify locally:

```bash
python -m build
python -c "import zipfile, glob; z=glob.glob('dist/*.whl')[0];\
print('\n'.join(sorted({p.split('/')[0] for p in zipfile.ZipFile(z).namelist()})))"
```

### Step 1: Update Version

Update version in `pyproject.toml`:

```toml
[project]
name = "genxai"
version = "0.1.0"  # Update this for each release
```

Version format: `MAJOR.MINOR.PATCH`
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes

### Step 2: Clean Previous Builds

```bash
# Remove old build artifacts
rm -rf dist/ build/ *.egg-info
```

### Step 3: Build Distribution

```bash
# Build source distribution and wheel
python -m build
```

This creates:
- `dist/genxai-0.1.0.tar.gz` (source distribution)
- `dist/genxai-0.1.0-py3-none-any.whl` (wheel)

### Step 4: Test on TestPyPI (Recommended)

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ genxai
```

**Note**: `--extra-index-url` allows installing dependencies from regular PyPI.

### Step 5: Publish to PyPI

Once tested, publish to production PyPI:

```bash
# Upload to PyPI
python -m twine upload dist/*
```

### Step 6: Verify Installation

```bash
# Install from PyPI
pip install genxai

# Test the core install
python -c "import genxai; print(genxai.__version__)"

# Verify the OSS CLI entry point is installed
genxai --help
genxai tool --help
genxai workflow --help
```

## Automated Publishing with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      
      - name: Build package
        run: python -m build
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: python -m twine upload dist/*
```

**Setup**:
1. Go to GitHub repo → Settings → Secrets → Actions
2. Add secret: `PYPI_API_TOKEN` with your PyPI API token
3. Create a release on GitHub to trigger publishing

## Release Checklist

Before publishing a new version:

- [ ] Update version in `pyproject.toml`
- [ ] Update `CHANGELOG.md` with changes
- [ ] Run tests: `pytest`
- [ ] Build locally: `python -m build`
- [ ] Test on TestPyPI
- [ ] Create git tag: `git tag v0.1.0`
- [ ] Push tag: `git push origin v0.1.0`
- [ ] Publish to PyPI
- [ ] Create GitHub release
- [ ] Verify installation: `pip install genxai`

## Version Management

### Semantic Versioning

Follow semantic versioning (semver):

- `0.1.0` → `0.1.1`: Bug fixes
- `0.1.0` → `0.2.0`: New features
- `0.1.0` → `1.0.0`: Breaking changes

### Pre-release Versions

For alpha/beta releases:

```toml
version = "0.1.0a1"  # Alpha
version = "0.1.0b1"  # Beta
version = "0.1.0rc1" # Release candidate
```

Install pre-releases:

```bash
pip install --pre genxai
```

## Troubleshooting

### Error: Package already exists

You cannot overwrite a published version. You must:
1. Increment the version number
2. Build and publish the new version

### Error: Invalid credentials

- Check your API token is correct
- Ensure `~/.pypirc` is properly formatted
- Verify token hasn't expired

### Error: Missing dependencies

Ensure all dependencies are listed in `pyproject.toml`:

```toml
dependencies = [
    "click>=8.1.0",
    "rich>=13.0.0",
    # ... other dependencies
]
```

### Error: Import errors after installation

Check that:
- All packages are included in `pyproject.toml`
- `__init__.py` files exist in all packages
- Entry points are correctly configured

## Best Practices

1. **Test Before Publishing**
   - Always test on TestPyPI first
   - Test installation in a clean virtual environment

2. **Version Control**
   - Tag releases in git
   - Keep CHANGELOG.md updated
   - Use semantic versioning

3. **Security**
   - Use API tokens (not passwords)
   - Enable 2FA on PyPI account
   - Keep `.pypirc` private

4. **Documentation**
   - Update README.md for each release
   - Include installation instructions
   - Document breaking changes

5. **Automation**
   - Use GitHub Actions for consistent releases
   - Automate testing before publishing
   - Auto-generate changelogs

## Resources

- [PyPI](https://pypi.org/)
- [TestPyPI](https://test.pypi.org/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)

## Quick Reference

```bash
# Build
python -m build

# Test on TestPyPI
python -m twine upload --repository testpypi dist/*

# Publish to PyPI
python -m twine upload dist/*

# Install from PyPI
pip install genxai

# Install specific version
pip install genxai==0.1.0

# Upgrade to latest
pip install --upgrade genxai
```
