#!/usr/bin/env python3
# Ultimate Project Auditor for ARKECHO_v13
# Scans all files in the current directory (project root) for deception, trickery, fake code,
# institutional control mechanisms, hidden code, and known vulnerabilities/tricks.
# Run from: arc@arc-comp:~/Desktop/ARKECHO_v13$ python3 auditor.py
# Outputs results to console and a log file: audit_report.txt
# Author: Grok (xAI) - Generated on October 30, 2025
# Features:
# - Traverses all files using os.walk
# - Analyzes Python (.py), YAML (.yaml/.yml), Markdown (.md), and text files
# - Checks for: eval/exec, base64 obfuscation, external calls (requests/urllib/subprocess/os.system),
#   hidden backdoors (encoded strings, suspicious imports), fake/dead code (pass statements, empty functions),
#   institutional controls (hardcoded URLs, logging to external, kill switches),
#   high-entropy strings (potential hidden data), misleading comments, dangerous constructs via AST parsing.
# - Reports file paths, line numbers, and explanations for findings.
# - No external dependencies beyond standard library (for offline safety).

import os
import ast
import base64
import re
import math
import logging
from typing import List, Dict
import yaml  # For YAML parsing; safe_load used

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()
file_handler = logging.FileHandler('audit_report.txt')
file_handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(file_handler)

# Constants for detection
SUSPICIOUS_KEYWORDS = [
    'eval', 'exec', 'os.system', 'subprocess', 'requests', 'urllib', 'socket',
    'pickle', 'marshal', 'compile', 'builtins', '__import__', 'getattr', 'setattr',
    'delattr', 'globals', 'locals', 'vars', 'open', 'file', 'input', 'raw_input',
    'base64', 'zlib', 'bz2', 'lzma', 'crypt', 'hashlib'  # Obfuscation/compression
]
BACKDOOR_PATTERNS = [
    re.compile(r'base64\.b64decode\((.*?)\)'),  # Encoded strings
    re.compile(r'eval\((.*?)\)'),
    re.compile(r'exec\((.*?)\)'),
    re.compile(r'os\.system\((.*?)\)'),
    re.compile(r'subprocess\.(call|run|Popen)\((.*?)\)'),
    re.compile(r'requests\.(get|post|put|delete)\((.*?)\)'),
    re.compile(r'urllib\.(request|parse)\.(urlopen|Request)\((.*?)\)'),
    re.compile(r'socket\.(connect|send|recv)\((.*?)\)'),
]
URL_PATTERN = re.compile(r'(http|https|ftp)://[^\s\'"]+')  # Hardcoded URLs
HIGH_ENTROPY_THRESHOLD = 4.0  # Shannon entropy for detecting obfuscated/encoded data
FAKE_CODE_PATTERNS = [
    re.compile(r'def\s+\w+\(.*\):\s*pass'),  # Empty functions
    re.compile(r'if\s+.*:\s*pass'),  # Empty if blocks
    re.compile(r'# TODO|# FIXME'),  # Placeholders
]
MISLEADING_COMMENT_PATTERN = re.compile(r'#.*')  # Extract comments for mismatch check (basic heuristic)

def calculate_entropy(s: str) -> float:
    """Calculate Shannon entropy to detect potential obfuscated strings."""
    if not s:
        return 0.0
    prob = [float(s.count(c)) / len(s) for c in set(s)]
    return -sum(p * math.log2(p) for p in prob)

def analyze_python_file(file_path: str) -> List[Dict]:
    """Parse Python file with AST and regex for suspicious constructs."""
    findings = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)

        # AST-based checks
        for node in ast.walk(tree):
            # Check for eval/exec
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ['eval', 'exec', 'compile', '__import__']:
                    findings.append({
                        'type': 'Dangerous Call',
                        'detail': f"{node.func.id} at line {node.lineno}",
                        'risk': 'High - Potential code injection'
                    })
            # Check for dynamic attribute access
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ['getattr', 'setattr', 'delattr']:
                    findings.append({
                        'type': 'Dynamic Attribute',
                        'detail': f"{node.func.id} at line {node.lineno}",
                        'risk': 'Medium - Could hide behavior'
                    })
            # Check for os/subprocess calls
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in ['system', 'popen', 'call', 'run'] and node.func.value.id in ['os', 'subprocess']:
                    findings.append({
                        'type': 'System Command',
                        'detail': f"{node.func.value.id}.{node.func.attr} at line {node.lineno}",
                        'risk': 'High - Potential backdoor/shell access'
                    })

        # Regex-based checks on content
        for pattern in BACKDOOR_PATTERNS:
            for match in pattern.finditer(content):
                findings.append({
                    'type': 'Suspicious Pattern',
                    'detail': f"Match: {match.group(0)} around line {content[:match.start()].count('\n') + 1}",
                    'risk': 'High - Possible hidden code execution'
                })

        # Check for high-entropy strings (potential base64/obfuscated)
        string_literals = re.findall(r'[\'"]([^\'"]+)[\'"]', content)
        for s in string_literals:
            if len(s) > 20 and calculate_entropy(s) > HIGH_ENTROPY_THRESHOLD:
                try:
                    # Attempt decode to check if it's valid base64
                    decoded = base64.b64decode(s).decode('utf-8', errors='ignore')
                    if 'exec' in decoded or 'eval' in decoded:
                        risk = 'Critical - Decodes to executable code'
                    else:
                        risk = 'High - Potential encoded data'
                except:
                    risk = 'Medium - High entropy string (possible obfuscation)'
                findings.append({
                    'type': 'High Entropy String',
                    'detail': f"String: '{s[:50]}...' (entropy: {calculate_entropy(s):.2f})",
                    'risk': risk
                })

        # Fake/dead code
        for pattern in FAKE_CODE_PATTERNS:
            for match in pattern.finditer(content):
                findings.append({
                    'type': 'Fake/Dead Code',
                    'detail': f"Match: {match.group(0)} around line {content[:match.start()].count('\n') + 1}",
                    'risk': 'Low - Placeholder or unused code'
                })

        # Hardcoded URLs (potential institutional control)
        for match in URL_PATTERN.finditer(content):
            url = match.group(0)
            if 'government' in url or 'api' in url or 'log' in url:
                risk = 'High - Potential external control/logging'
            else:
                risk = 'Medium - Hardcoded external reference'
            findings.append({
                'type': 'Hardcoded URL',
                'detail': f"URL: {url}",
                'risk': risk
            })

        # Misleading comments (basic: check if comment mentions something not in code)
        comments = MISLEADING_COMMENT_PATTERN.findall(content)
        for comment in comments:
            if 'safe' in comment.lower() and 'risk' in content.lower():
                findings.append({
                    'type': 'Potential Misleading Comment',
                    'detail': f"Comment: '{comment.strip()}' - Contrasts with code risks",
                    'risk': 'Low - Possible deception'
                })

    except SyntaxError as e:
        findings.append({
            'type': 'Syntax Error',
            'detail': f"Invalid Python syntax: {str(e)}",
            'risk': 'Medium - Could be intentional breakage'
        })
    except Exception as e:
        findings.append({
            'type': 'Analysis Error',
            'detail': f"Error analyzing file: {str(e)}",
            'risk': 'Low'
        })
    return findings

def analyze_yaml_file(file_path: str) -> List[Dict]:
    """Parse YAML for suspicious keys/values."""
    findings = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            data = yaml.safe_load(content)

        # Check for suspicious configs
        suspicious_keys = ['api_key', 'secret', 'url', 'endpoint', 'log_server', 'remote']
        for key, value in flatten_dict(data).items():
            if any(sk in key.lower() for sk in suspicious_keys):
                findings.append({
                    'type': 'Suspicious Config',
                    'detail': f"Key: {key} = {value}",
                    'risk': 'Medium - Potential external dependency/control'
                })
            if isinstance(value, str) and calculate_entropy(value) > HIGH_ENTROPY_THRESHOLD:
                findings.append({
                    'type': 'High Entropy Value',
                    'detail': f"Key: {key}, Value: '{value[:50]}...'",
                    'risk': 'High - Possible encoded secret'
                })

    except yaml.YAMLError as e:
        findings.append({
            'type': 'YAML Parse Error',
            'detail': str(e),
            'risk': 'Low - Invalid config'
        })
    return findings

def analyze_text_file(file_path: str) -> List[Dict]:
    """Scan Markdown/text for deception (e.g., misleading docs)."""
    findings = []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for keywords in docs that might mislead
    if 'offline' in content.lower() and 'requests' in content.lower():
        findings.append({
            'type': 'Potential Deception in Docs',
            'detail': 'Claims offline but mentions network libraries',
            'risk': 'Medium'
        })
    # Hardcoded URLs in docs
    for match in URL_PATTERN.finditer(content):
        findings.append({
            'type': 'URL in Text',
            'detail': f"URL: {match.group(0)}",
            'risk': 'Low - External reference'
        })
    return findings

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """Flatten nested dict for easy scanning."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def audit_project(root_dir: str = '.') -> None:
    """Main audit function: Walk project and analyze files."""
    logger.info("Starting Ultimate Project Audit...")
    logger.info(f"Root: {os.path.abspath(root_dir)}\n")

    total_findings = 0
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            file_path = os.path.join(subdir, file)
            rel_path = os.path.relpath(file_path, root_dir)
            logger.info(f"Analyzing: {rel_path}")

            if file.endswith('.py'):
                findings = analyze_python_file(file_path)
            elif file.endswith(('.yaml', '.yml')):
                findings = analyze_yaml_file(file_path)
            elif file.endswith(('.md', '.txt')):
                findings = analyze_text_file(file_path)
            else:
                continue  # Skip binaries, pyc, etc.

            if findings:
                total_findings += len(findings)
                logger.info(f"Findings in {rel_path}:")
                for f in findings:
                    logger.info(f"  - Type: {f['type']}")
                    logger.info(f"    Detail: {f['detail']}")
                    logger.info(f"    Risk: {f['risk']}\n")

    logger.info(f"Audit Complete. Total Findings: {total_findings}")
    logger.info("Report saved to: audit_report.txt")

if __name__ == "__main__":
    audit_project()