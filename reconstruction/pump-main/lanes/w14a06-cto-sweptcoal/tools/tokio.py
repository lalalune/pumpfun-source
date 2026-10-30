import sys
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import ctoracle as co
from pathlib import Path
def toks(p):
    if p.endswith('.so'): return co.so_tokens(p)[0]
    raw=Path(p).read_bytes(); out=[];i=0
    while i<len(raw):
        n=16 if raw[i]==0x18 else 8; out.append(raw[i:i+n]); i+=n
    return out
