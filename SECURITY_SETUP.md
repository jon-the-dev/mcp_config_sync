# Security Setup Guide

This guide helps you set up comprehensive security checks for your Python applications to prevent vulnerabilities like path traversals.

## Quick Setup

1. **Install security tools:**

   ```bash
   python setup-security.py
   ```

2. **Manual installation (if needed):**

   ```bash
   pip install -r requirements-security.txt
   pre-commit install
   ```

## Security Tools Included

### GitHub Actions

- **Bandit**: Python security linter that detects common security issues
- **Safety**: Checks dependencies for known vulnerabilities  
- **Semgrep**: Static analysis tool with custom path traversal rules
- **CodeQL**: GitHub's semantic code analysis
- **Dependency Review**: Scans for vulnerable dependencies in PRs

### Pre-commit Hooks

- **Bandit**: Runs on every commit to catch security issues early
- **Safety**: Checks dependencies before commits
- **Semgrep**: Custom rules for path traversal detection
- **Detect-secrets**: Prevents accidental secret commits
- **Code quality**: Black, isort, flake8, mypy for clean code

## Path Traversal Protection

### Using the Security Utils

```python
from security_utils import SecurePathValidator, secure_open, PathTraversalError

# Validate paths
if SecurePathValidator.is_safe_path(user_input, allowed_base="/safe/directory"):
    # Safe to use
    pass

# Secure file operations
try:
    with secure_open(user_filename, 'r', allowed_base="/uploads") as f:
        content = f.read()
except PathTraversalError:
    # Handle attack attempt
    pass

# Sanitize filenames
safe_filename = SecurePathValidator.sanitize_filename(user_input)
```

### Custom Semgrep Rules

The `.semgrep/path-traversal.yml` file includes rules that detect:

- Direct user input in `open()` calls
- Unsafe `os.path.join()` usage
- Dangerous file operations with user input
- Flask file serving vulnerabilities

## Running Security Checks

### Manual Scans

```bash
# Run all security tools
bandit -r . --severity-level medium
safety check
semgrep --config=auto .

# Check for secrets
detect-secrets scan --baseline .secrets.baseline

# Run pre-commit on all files
pre-commit run --all-files
```

### GitHub Actions

Security checks run automatically on:

- Every push to main/master/develop branches
- Every pull request
- Dependency changes (dependency review)

## Configuration Files

- `.bandit`: Bandit configuration focusing on file system security
- `.pre-commit-config.yaml`: Pre-commit hooks configuration
- `.semgrep/path-traversal.yml`: Custom path traversal detection rules
- `.github/workflows/security-checks.yml`: GitHub Actions workflow

## Common Path Traversal Patterns Detected

The security tools will catch these dangerous patterns:

- `../../../etc/passwd` (directory traversal)
- `..\\..\\windows\\system32` (Windows traversal)
- `/etc/passwd` (absolute paths to sensitive files)
- `~/.ssh/id_rsa` (home directory access)
- URL-encoded traversal attempts
- Null byte injection

## Best Practices

1. **Always validate user input** before file operations
2. **Use allowlists** instead of blocklists for allowed paths
3. **Resolve paths** and check they stay within allowed directories
4. **Sanitize filenames** to remove dangerous characters
5. **Use the security utilities** provided in this setup
6. **Run security scans regularly** in CI/CD
7. **Keep dependencies updated** to avoid known vulnerabilities

## Troubleshooting

### Pre-commit Issues

```bash
# Update pre-commit hooks
pre-commit autoupdate

# Skip hooks temporarily (not recommended)
git commit --no-verify
```

### False Positives

Add exclusions to `.bandit` or use `# nosec` comments:

```python
# This is safe because input is validated
open(validated_path, 'r')  # nosec B102
```

### Secrets Detection

Update the baseline when adding legitimate secrets patterns:

```bash
detect-secrets scan --baseline .secrets.baseline --force-use-all-plugins
```

## Integration with Existing Projects

1. Copy the configuration files to your project
2. Run `python setup-security.py`
3. Commit the security configuration
4. Address any security findings
5. Security checks will run automatically going forward
