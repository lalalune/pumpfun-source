import sys,json
sys.path.insert(0,sys.argv[1])
from coords import sites, ORIG, OS, original_windows
from score import sections, body
from elf_symbols import function_symbols
pat=sys.argv[3]
out={'orig':[], 'cand':[]}
for w in original_windows():
    for s in sites(ORIG,OS,w['start'],w['raw']):
        if pat in s['path']: out['orig'].append((hex(w['start']),s['slot'],s['line']))
blob=open(sys.argv[2],'rb').read(); cs=sections(blob)
for (a,n,nm) in function_symbols(blob):
    for s in sites(blob,cs,a,body(blob,cs,a,n)):
        if pat in s['path']: out['cand'].append((nm[:70],s['slot'],s['line']))
print(json.dumps(out))
