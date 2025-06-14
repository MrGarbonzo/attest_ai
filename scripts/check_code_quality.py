#!/usr/bin/env python3
"""
Code quality checks for attest_ai
Checks for potential security issues while avoiding false positives
"""

import os
import re
import sys
from pathlib import Path

# Patterns that indicate actual secrets (not just variable names)
SECRET_PATTERNS = [
    # Actual password assignments with values
    r'(?:password|passwd|pwd)[\s]*[:=][\s]*["\'][a-zA-Z0-9@#$%^&*()_+\-=\[\]{};:,.<>?]{8,}["\']',
    # API key assignments with actual key patterns
    r'(?:api_key|apikey|API_KEY)[\s]*[:=][\s]*["\'][a-zA-Z0-9]{20,}["\']',
    # Token assignments with actual tokens
    r'(?:token|TOKEN)[\s]*[:=][\s]*["\'][a-zA-Z0-9\-_.]{20,}["\']',
    # AWS-style keys
    r'(?:AKIA|ASIA)[A-Z0-9]{16}',
    # Private keys
    r'-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----',
    # Base64 encoded secrets (at least 40 chars)
    r'(?:secret|SECRET)[\s]*[:=][\s]*["\'][a-zA-Z0-9+/]{40,}={0,2}["\']',
]

# Patterns to exclude (false positives)
EXCLUDE_PATTERNS = [
    r'SECRET_AI',  # This is a service name, not a secret
    r'secret_ai',  # Variable names for Secret AI service
    r'SecretAI',   # Class names
    r'from \..*secret',  # Import statements
    r'import.*secret',   # Import statements
    r'class.*Secret',    # Class definitions
    r'def.*secret',      # Function definitions
    r'_client',          # Client variable names
    r'\.secret',         # Attribute access
    r'get_settings',     # Settings access
    r'Field\(',          # Pydantic field definitions
    r'BaseSettings',     # Settings class
    r'# ',               # Comments
    r'cache_key',        # Cache key variables
    r'_KEY\s*=\s*["\'][A-Z_]+["\']',  # Constant definitions
    r'ErrorCode\.',      # Error code enums
    r'secretvm',         # SecretVM references (lowercase)
    r'SecretVM',         # SecretVM references (camelcase)
]

def check_file(filepath):
    """Check a single file for potential secrets"""
    issues = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        # Skip empty lines
        if not line.strip():
            continue
            
        # Check if line should be excluded
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in EXCLUDE_PATTERNS):
            continue
        
        # Check for secret patterns
        for pattern in SECRET_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                issues.append({
                    'file': filepath,
                    'line': line_num,
                    'content': line.strip(),
                    'pattern': pattern
                })
                break
    
    return issues

def main():
    """Run code quality checks"""
    print("🔍 Running code quality checks...")
    
    # Find all Python files in src/
    src_dir = Path(__file__).parent.parent / 'src'
    python_files = list(src_dir.rglob('*.py'))
    
    all_issues = []
    
    for filepath in python_files:
        issues = check_file(filepath)
        all_issues.extend(issues)
    
    # Check for dangerous functions
    dangerous_patterns = [
        (r'\beval\s*\(', 'eval() usage'),
        (r'\bexec\s*\(', 'exec() usage'),
        (r'subprocess\.call\s*\(', 'subprocess.call() usage - use subprocess.run() instead'),
        (r'os\.system\s*\(', 'os.system() usage - use subprocess instead'),
    ]
    
    for filepath in python_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        for pattern, description in dangerous_patterns:
            if re.search(pattern, content):
                print(f"⚠️  {description} found in {filepath}")
    
    # Report results
    if all_issues:
        print("\n❌ Potential security issues found:")
        for issue in all_issues:
            print(f"\n  File: {issue['file']}")
            print(f"  Line {issue['line']}: {issue['content']}")
        
        print(f"\n❌ Found {len(all_issues)} potential security issues")
        return 1
    else:
        print("✅ No hardcoded secrets found")
        print("✅ Code quality checks passed")
        return 0

if __name__ == "__main__":
    sys.exit(main())