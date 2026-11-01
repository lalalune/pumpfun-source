import re,collections,sys
def calls(p):
    t=open(p).read()
    m=re.search(r'^define[^\n]*admin_cto7execute17h[^\n]*\n',t,re.M)
    s=m.start(); e=t.index('\n}\n',s)
    body=t[s:e]
    c=collections.Counter(re.findall(r'call [^@]*(@"[^"]+"|@[\w.$-]+)\(',body))
    return c,body
F,bf=calls(sys.argv[1]); A,ba=calls(sys.argv[2])
print(len(bf.split('\n')),len(ba.split('\n')))
for k in sorted(set(F)|set(A)):
    if F[k]!=A[k]: print(F[k],A[k],k[:150])
# compare instruction opcode histograms
def hist(b):
    return collections.Counter(re.findall(r'^\s+(?:%[\w.$"-]+ = )?(\w+)',b,re.M))
hf,ha=hist(bf),hist(ba)
for k in sorted(set(hf)|set(ha)):
    if hf[k]!=ha[k]: print('op',k,hf[k],ha[k])
