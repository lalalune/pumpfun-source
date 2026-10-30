#!/usr/bin/env python3
"""getfn.py <pump_recovered.ll> <out_dir>: trim the module to execute (mod.ll) and write execute's body (fn.ll)."""
import sys, subprocess, os
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ctoracle as co
src, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
d = os.path.dirname(os.path.abspath(__file__))
subprocess.run([sys.executable, f'{d}/trim.py', str(src), str(out/'t1.ll')], check=True, capture_output=True)
subprocess.run([sys.executable, f'{d}/trim2.py', str(out/'t1.ll'), str(out/'mod.ll')], check=True, capture_output=True)
(out/'t1.ll').unlink()
mod = (out/'mod.ll').read_text(); sym = co.SYMRE.search(mod).group(0); i, j = co.fn_bounds(mod, sym)
(out/'fn.ll').write_text(mod[i:j])
