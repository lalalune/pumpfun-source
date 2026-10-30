#!/usr/bin/env python3
"""Assemble the fixed offline public registry from explicit locked archives only."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from replay import prepare_registry

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archives', type=Path, required=True,
                   help='flat directory containing the 253 Cargo.lock-verified .crate archives')
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    prepare_registry(a.archives, a.out)
