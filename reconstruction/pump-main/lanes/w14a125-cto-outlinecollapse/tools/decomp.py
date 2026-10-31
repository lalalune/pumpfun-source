#!/usr/bin/env python3
"""decomp.py <rxname>...: collapse decomposition row: bytes, M, fR/rfR/rfjR (fbound legal-frame bounds), the validate-exit
join flip (jfix3 relayout: moved blocks, relaid M and its fbound), and the REAL 307/312 outline state (inl.py)."""
import sys,os,subprocess,json,re
D=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); JT=D+'/jt'
def fb(o):
    r=subprocess.run(['python3',JT+'/fbound.py',o],capture_output=True,text=True,cwd=JT).stdout.strip().split('\n')[-1]
    return json.loads(r[r.index('{'):])
print('| name | bytes | M | fR | rfR | rfjR | J moved | relaid bytes | relaid M | relaid fR | relaid rfR | relaid rfjR | 307/312 |')
print('| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |')
for n in sys.argv[1:]:
    a=fb(f'{D}/rx/{n}/m.o')
    j=subprocess.run(['python3',JT+'/jfix3.py',f'{D}/rx/{n}/m.ll',f'{D}/jf/{n}'],capture_output=True,text=True,cwd=JT).stdout.strip().split('\n')[-1]
    try: j=json.loads(j)
    except Exception: j={'note':'err '+j[-100:]}
    rel=['','','','','','']
    if 'moved' in j:
        b=fb(f'{D}/jf/{n}_re.o'); rel=[j['moved'],b['bytes'],b['M'],b['fR'],b['rfR'],b['rfjR']]
    else: rel=[0]+['=']*5
    il=subprocess.run(['python3',D+'/tools/inl.py',n],capture_output=True,text=True).stdout
    p=' '.join(x for x in il.split() if x[:3] in ('307','312'))
    print(f"| {n} | {a['bytes']} | {a['M']} | {a['fR']} | {a['rfR']} | {a['rfjR']} | "+' | '.join(str(x) for x in rel)+f" | {p} |")
