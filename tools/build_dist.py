# tools/build_dist.py
# ArkEcho Systems (c) 2025. All Rights Reserved.
"""
Build a distribution package for ArkEcho.
"""
import subprocess
import sys

if __name__ == "__main__":
    # Upgrade build tools if needed
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "setuptools", "wheel"], check=True)
    # Build source distribution
    subprocess.run([sys.executable, "setup.py", "sdist"], check=True)
