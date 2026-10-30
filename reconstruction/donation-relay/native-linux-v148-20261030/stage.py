#!/usr/bin/env python3
"""Validate measured inputs and stage a fresh path-only native Relay replay plan."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from replay import stage

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['repo', 'sdk', 'registry', 'work']:
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(stage(a.repo, a.sdk, a.registry, a.work), indent=2))
