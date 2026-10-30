#!/usr/bin/env python3
"""apply.py <module> <mut,mut,...> : apply mutations to the worktree's multi_hop_curve_swap.rs in place."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import hc as hillclimb
mod = __import__(sys.argv[1]); muts = [x for x in sys.argv[2].split(",") if x]
p = Path(__file__).resolve().parents[4] / hillclimb.REL
t = hillclimb.apply(p.read_text(), muts, {m: (o, n) for m, o, n in mod.M})
assert t is not None, "mutation does not apply"
p.write_text(t); print("applied", muts)
