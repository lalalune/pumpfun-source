#!/usr/bin/env python3
"""Diagnostic: mark every subset of non-panic call sites in v3_buy_costs cold; llc; diff vs original."""
import re,os,sys,subprocess,itertools,difflib
from concurrent.futures import ThreadPoolExecutor
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w4-v3costs'); SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools')
t=open(O+'/ir/base/one.ll').read()
m=re.search(r'^define[^\n]*12v3_buy_costs[^\n]*\{\n.*?^\}\n',t,re.M|re.S); f=m.group(0); sym=re.search(r'@(\S+?)\(',f).group(1)
lines=f.split('\n')
idx=[i for i,l in enumerate(lines) if not l.lstrip().startswith(';') and re.search(r'\bcall ',l) and 'llvm.' not in l and 'unwrap_failed' not in l and 'expect_failed' not in l]
o=[re.sub(r'([+-]0x[0-9a-f]+)$','J',l.strip()) if re.match(r'(ja|j[a-z]+ )',l.strip()) else l.strip() for l in open(O+'/notes/orig-norm.txt').read().splitlines()]
def run(sub):
    L=lines[:]
    for i in sub: L[i]=re.sub(r'#27$','#99',L[i]) if L[i].endswith('#27') else L[i]+' #99'
    t2=t[:m.start()]+'\n'.join(L)+t[m.end():]+'\nattributes #99 = { cold nounwind }\n'
    d=O+'/tmp/cc/'+'_'.join(map(str,sub)); os.makedirs(d,exist_ok=True)
    open(d+'/m.ll','w').write(t2)
    r=subprocess.run([SDK+'/llvm/bin/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',d+'/m.ll','-filetype=obj','-o',d+'/m.o'],capture_output=True,text=True)
    if r.returncode: return (999,sub,r.stderr[:200])
    fn=subprocess.run(['sh',O+'/bin/fn.sh',d+'/m.o',sym],capture_output=True,text=True).stdout
    fn=re.sub(r'call -?0x[0-9a-f]+','call X',fn); fn=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',fn)
    c=[re.sub(r'([+-]0x[0-9a-f]+)$','J',l.strip()) if re.match(r'(ja|j[a-z]+ )',l.strip()) else l.strip() for l in fn.splitlines()]
    diff=[l for l in difflib.unified_diff(o,c,n=0,lineterm='') if l[:1] in '+-' and l[:3] not in ('+++','---')]
    subprocess.run(['rm','-rf',d])
    return (len(diff),sub,sum(16 if l.startswith('lddw') else 8 for l in c))
subs=[s for k in range(1,len(idx)+1) for s in itertools.combinations(idx,k)]
maxk=int(sys.argv[1]) if len(sys.argv)>1 else 99
subs=[s for s in subs if len(s)<=maxk]
print('calls',[(i,re.search(r'@("[^"]+"|\S+?)\(',lines[i]).group(1)[-40:]) for i in idx],len(subs),flush=True)
with ThreadPoolExecutor(8) as ex: res=list(ex.map(run,subs))
res.sort()
for r in res[:25]: print(r)
