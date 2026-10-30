#!/usr/bin/env python3
"""Print the validated replay command; --execute starts one fresh guarded build."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from replay import execute, validate_staged

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--execute', action='store_true')
    a = p.parse_args()
    result = execute(a.work) if a.execute else validate_staged(a.work)
    print(json.dumps(result, indent=2))
    if a.execute:
        raise SystemExit(0 if result.get('canonicalOutputHashesEqual') else 1)
