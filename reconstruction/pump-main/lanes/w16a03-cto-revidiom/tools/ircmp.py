"""ircmp.py <a> <b>: compare the post-opt execute of two rx runs: allocas, call targets, block count."""
import sys,re,collections
R='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a03-cto-revidiom/rx/'
def fn(name):
    t=open(R+name+'/m.ll').read()
    m=re.search(r'^define [^\n]*admin_cto7execute17h[^\n]*$',t,re.M); s=m.start(); e=t.find('\n}\n',s); return t[s:e+3]
def summ(f):
    al=re.findall(r'%([\w.]+) = alloca \[(\d+) x i8\]',f)
    calls=re.findall(r'call [^@]*@"?([\w$.]+)"?\(',f)
    blocks=len(re.findall(r'^[\w.$"]+:',f,re.M))
    return al,collections.Counter(calls),blocks
a,b=sys.argv[1],sys.argv[2]
A=summ(fn(a)); B=summ(fn(b))
print('blocks',A[2],B[2])
sa={x for x in A[0]}; sb={x for x in B[0]}
print('allocas only in',a,sorted(sa-sb)); print('allocas only in',b,sorted(sb-sa))
ca,cb=A[1],B[1]
for k in sorted(set(ca)|set(cb)):
    if ca[k]!=cb[k] and not k.startswith('llvm.'): print(f'  call {k[:100]}: {ca[k]} -> {cb[k]}')
