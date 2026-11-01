import re,os,difflib,sys
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w19b13-cto-v1-holder-and1')
def body(n):
    t=open(f'{OUT}/fx/{n}/m.ll').read()
    m=re.search(r'^define [^\n]*admin_cto7execute[^\n]*\{\n',t,re.M); e=t.index('\n}\n',m.end()); b=t[m.start():e]
    b=re.sub(r', !(noalias|alias\.scope|prof|range|nonnull|noundef|align) !\d+','',b)
    b=re.sub(r'%(\d+)\b','%N',b)
    b=re.sub(r'#\d+','#A',b)
    b=re.sub(r'metadata !\d+','metadata !M',b)
    return b.split('\n')
a=body(sys.argv[1]); b=body(sys.argv[2])
n=0; lim=int(sys.argv[3]) if len(sys.argv)>3 else 60
for l in difflib.unified_diff(a,b,lineterm='',n=0):
    print(l[:190]); n+=1
    if n>lim: break
