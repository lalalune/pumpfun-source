#!/usr/bin/env python3
"""scan.py <base.ll> <prefix> <knobs.txt> <results.jsonl> [--opt] [-j N]
knobs.txt lines: name|flags. Without --opt: llc flags on the (post-opt) base. With --opt: flags are
opt flags applied with -O3 to the (pre-opt) base, then default llc."""
import sys,subprocess,json,os,concurrent.futures as cf
L=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w12a10-cto-optoracle')
a=sys.argv[1:]; opt='--opt' in a; a=[x for x in a if x!='--opt']
j=4
if '-j' in a: k=a.index('-j'); j=int(a[k+1]); a=a[:k]+a[k+2:]
base,prefix,knobs,res=a
rows=[l.rstrip('\n').split('|',1) for l in open(knobs) if l.strip() and not l.startswith('#')]
def run(r):
    n,f=r
    if opt: cmd=['python3',L+'/tools/oracle.py',base,prefix+'-'+n,'--opt','-O3 '+f]
    else: cmd=['python3',L+'/tools/oracle.py',base,prefix+'-'+n,'--']+f.split()
    p=subprocess.run(cmd,capture_output=True,text=True)
    try: d=json.loads(p.stdout.strip().splitlines()[-1])
    except Exception: d={'err':(p.stdout+p.stderr)[-300:]}
    d['knob']=n; d['flags']=f
    # cleanup big files
    dd=L+'/irexp/'+prefix+'-'+n
    for fn in ('opt.ll','m.ll'):
        try: os.remove(dd+'/'+fn)
        except OSError: pass
    return d
with open(res,'a') as o, cf.ThreadPoolExecutor(j) as ex:
    for d in ex.map(run,rows):
        o.write(json.dumps(d)+'\n'); o.flush()
out=[json.loads(l) for l in open(res)]
for d in sorted(out,key=lambda d:-d.get('ratio',-1)):
    print('%.5f %6s %-30s %s'%(d.get('ratio',-1),d.get('bytes','-'),d['knob'],d['flags'] if 'err' not in d else d['err'][-100:]))
