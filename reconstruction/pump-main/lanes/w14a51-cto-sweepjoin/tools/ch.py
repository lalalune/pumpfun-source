#!/usr/bin/env python3
"""ch3.py <name...>: per 0x800 orig chunk matched counts for raw(jump-masked)/fm/sk for rx/<name>/m.o; first name is reference."""
import sys,os,difflib,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import absratio as A, re
class CR:
    @staticmethod
    def nr(s):
        s=re.sub(r'\s+<[^>]*>','',s.strip())
        if s.startswith('call'): return 'call'
        s=re.sub(r'^lddw (r\d+), .*',r'lddw \1',s)
        if s.startswith('j'): s=re.sub(r'[+-]0x[0-9a-f]+$|[+-]\d+$','J',s)
        return s
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a51-cto-sweepjoin')
def dis(n):
    p=n if ('/' in n) else f'{O}/rx/{n}/m.o'
    t=subprocess.run(['bash',O+'/tools/disso.sh',p],capture_output=True,text=True).stdout
    return [l.split(None,1)[1] for l in t.split('\n') if len(l.split(None,1))>1]
def hits(Ov,C):
    sm=difflib.SequenceMatcher(None,Ov,C,autojunk=False); h=[0]*len(Ov)
    for b in sm.get_matching_blocks():
        for k in range(b.size): h[b.a+k]=1
    return h
K=[('raw',CR.nr,None),('fm',lambda s:A.norm(s,False),None),('sk',lambda s:A.norm(s,True),None)]
a=sys.argv[1:]; ch=int(a.pop(0)[2:],16)//8 if a and a[0].startswith('-c') else 128; lo=0
if a and a[0].startswith('-f'): lo=int(a.pop(0)[2:],16)//8
names=a; res={}
for n in names:
    C=dis(n); res[n]={}
    for k,f,_ in K: res[n][k]=hits([f(x) for x in A.O],[f(x) for x in C])
N=len(A.O)
print('chunk   '+'  '.join(f'{n[:14]:>14s}' for n in names)+'   (raw/fm/sk)')
for i in list(range(lo,N,ch))+['tot']:
    row=[]
    for n in names:
        v=[sum(res[n][k][i:i+ch]) if i!='tot' else sum(res[n][k]) for k,_,_ in K]
        if n!=names[0]:
            r=[sum(res[names[0]][k][i:i+ch]) if i!='tot' else sum(res[names[0]][k]) for k,_,_ in K]; v=[f'{a-b:+d}' for a,b in zip(v,r)]
        row.append('/'.join(map(str,v)))
    print(f'{i*8:#07x} ' if i!='tot' else 'total   ', '  '.join(f'{x:>14s}' for x in row))
