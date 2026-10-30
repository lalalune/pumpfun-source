#!/usr/bin/env python3
"""Extract only the authenticated measured SDK subset; never executes a tool."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from replay import extract_sdk

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    extract_sdk(a.archive, a.out)
