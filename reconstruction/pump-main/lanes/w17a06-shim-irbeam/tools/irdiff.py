import re,difflib,sys
def body(p,pat=r'admin_cto7execute17h'):
    t=open(p).read()
    m=re.search(r'^define[^\n]*'+pat+r'[^\n]*\n',t,re.M)
    s=m.start(); e=t.index('\n}\n',s)
    return t[s:e].split('\n')
def norm(l):
    l=re.sub(r'%[\w.$-]+|%"[^"]+"','%v',l); l=re.sub(r'!\d+','!m',l); l=re.sub(r'^\w[\w.$-]*:.*','LABEL',l)
    return l
a=[norm(x) for x in body(sys.argv[1])]; b=[norm(x) for x in body(sys.argv[2])]
d=list(difflib.unified_diff(a,b,lineterm='',n=1))
print(len(d))
print('\n'.join(x[:250] for x in d[:int(sys.argv[3]) if len(sys.argv)>3 else 80]))
