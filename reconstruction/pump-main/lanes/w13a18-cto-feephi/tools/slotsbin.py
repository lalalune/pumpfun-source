import sys,importlib.util
spec=importlib.util.spec_from_file_location('s','/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a18-cto-feephi/tools/slots.py')
sys.argv_save=sys.argv; 
src=open(spec.origin).read().split('\nfor p in sys.argv[1:]:')[0]
g={'__file__':spec.origin}; exec(src,g)
for p in sys.argv[1:]:
    raw=g['fn']('orig') if p=='orig' else open(p,'rb').read()
    rows=sorted(g['scan'](raw),key=lambda r:r[2]); print(p[-20:],' '.join(f'{l}:{x:x}' for l,c,x in rows))
