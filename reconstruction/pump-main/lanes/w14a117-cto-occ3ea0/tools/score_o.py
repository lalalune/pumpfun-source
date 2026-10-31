import sys,os
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); g={'__name__':'x'}; exec(src.split("OUT=os.environ")[0],g)
O=g['orig_window'](); bs=os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so'); MM=g['mask'](g['elf_fn'](bs,g['KEEP']))
for f in sys.argv[1:]:
    c=g['elf_fn'](f,g['KEEP']); r,sd=g['metric'](c,O); print(f,round(r,5),sd,len(c),g['mask'](c)==MM)
