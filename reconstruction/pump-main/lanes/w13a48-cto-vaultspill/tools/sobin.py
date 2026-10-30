#!/usr/bin/env python3
"""sobin.py <unstripped.so> <out fn.bin>: admin_cto tokens (scorer-normalized) from a linked build."""
import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ctoracle
t,n=ctoracle.so_tokens(sys.argv[1]); open(sys.argv[2],'wb').write(b''.join(t))
