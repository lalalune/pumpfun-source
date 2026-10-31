import sys; A=sys.argv[:]
import sys,json; sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a104-cto-brhead/tools'); sys.argv=['x']
import relayn
def go(base,variants):
    for nm,spec in variants:
        r=relayn.run_rev(base,f'tmp/h/{nm}.s',spec); print(f'{nm:6s}',json.dumps(r))
if __name__=='__main__':
    V=[l.split(None,1) for l in open(A[2]).read().strip().split('\n') if l.strip() and not l.startswith('#')]
    go(A[1],[(a,b.strip()) for a,b in V])
