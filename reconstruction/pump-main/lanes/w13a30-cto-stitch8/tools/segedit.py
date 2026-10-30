import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import segscan
def edit(f):
    return segscan.apply(f.split('\n'), [m for m in os.environ['MOVES'].split(',') if m])
