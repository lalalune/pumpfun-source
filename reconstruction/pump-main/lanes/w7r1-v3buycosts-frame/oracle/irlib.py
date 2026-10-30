"""Diagnostic IR helpers for v3_buy_costs (lane w7r1-v3buycosts-frame). Not for proposals."""
import re,subprocess,os,difflib,tempfile
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-v3buycosts-frame')
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools')
BASE=os.environ.get('IRBASE',OUT+'/ir/base/one.ll')
def load():
    t=open(BASE).read()
    m=re.search(r'^define[^\n]*12v3_buy_costs[^\n]*\{\n.*?^\}\n',t,re.M|re.S)
    return t,m
def norm(lines):
    return [re.sub(r'([+-]0x[0-9a-f]+)$','J',l.strip()) if re.match(r'(ja|j[a-z]+ )',l.strip()) else l.strip() for l in lines]
ORIG=norm(open(OUT+'/notes/orig-norm.txt').read().splitlines())
_T=None
def run(f2,tag='x',keep=False,extra=(),suffix=''):
    global _T
    if _T is None: _T=load()
    t,m=_T; sym=re.search(r'@(\S+?)\(',m.group(0)).group(1)
    t2=t[:m.start()]+f2+t[m.end():]+suffix
    d=tempfile.mkdtemp(prefix=tag,dir=OUT+'/tmp') if not keep else OUT+'/irexp/'+tag
    os.makedirs(d,exist_ok=True)
    open(d+'/m.ll','w').write(t2)
    r=subprocess.run([SDK+'/llvm/bin/llc','-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext',d+'/m.ll','-filetype=obj','-o',d+'/m.o',*extra],capture_output=True,text=True)
    if r.returncode: return None,r.stderr[-800:]
    fn=subprocess.run(['sh',OUT+'/bin/fn.sh',d+'/m.o',sym],capture_output=True,text=True).stdout
    fn=re.sub(r'call -?0x[0-9a-f]+','call X',fn); fn=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',fn)
    c=norm(fn.splitlines())
    if not keep: subprocess.run(['rm','-rf',d])
    diff=[l for l in difflib.unified_diff(ORIG,c,n=0,lineterm='')]
    mi=sum(1 for l in diff if l[:1]=='-' and l[:3]!='---'); pl=sum(1 for l in diff if l[:1]=='+' and l[:3]!='+++')
    sz=sum(16 if l.startswith('lddw') else 8 for l in c)
    return (sz,mi,pl),diff
def blocks(f):
    """list of (label, text) blocks of function body"""
    body=f.split('{\n',1)[1].rsplit('}\n',1)[0]
    parts=re.split(r'\n(?=(?:"[^"]+"|[\w.$]+):)',body)
    out=[]
    for i,p in enumerate(parts):
        if i==0: out.append(('start',p)); continue
        lab=re.match(r'("[^"]+"|[\w.$]+):',p).group(1)
        out.append((lab,p))
    return out
def term_succs(btext):
    last=[l for l in btext.strip().split('\n') if l.strip()][-1]
    return re.findall(r'label %("[^"]+"|[\w.$]+)',last)
