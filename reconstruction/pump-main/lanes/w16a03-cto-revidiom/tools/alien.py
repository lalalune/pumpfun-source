"""alien.py: 4-gram shapes of MAIN's admin_cto that occur neither in the original admin_cto nor in any matched window,
mapped to main's admin_cto.rs source line through the line-table build. Lists the source constructs that produce shapes
the original program never produces."""
import sys,os,pickle,collections,difflib,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import shape,runs,srcmap
idx=pickle.load(open(shape.OUT+'/idx_n4_1.pkl','rb'))
O=runs.cto_insns('orig'); M=runs.cto_insns('main')
def grams(S): return [shape.shape_seq([x[2] for x in S[i:i+4]],keep_off=True) for i in range(len(S)-3)]
go=set(grams(O)); gm=grams(M)
files,funcs=srcmap._files,srcmap._funcs
f=[k for k in funcs if 'admin_cto7execute' in k][0]; body=funcs[f]
A=[t.split()[0] for a,t,p in M]; B=[s.split()[0] for s,l in body]
mp={}
for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,A,B,autojunk=False).get_opcodes():
    if tag=='equal':
        for k in range(i2-i1): mp[i1+k]=j1+k
cto_file=[k for k,v in files.items() if v.endswith('creator/admin_cto.rs')][0]
def line_of(i):
    k=i
    while k>=0 and k not in mp: k-=1
    if k<0: return None
    j=mp[k]
    while j>=0:
        l=body[j][1]
        if l and l[0]==cto_file: return (l[1],l[2])
        j-=1
    return None
src=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a03-cto-revidiom/programs/pump/src/creator/admin_cto.rs').read().split('\n')
agg=collections.Counter(); ex={}
n=0
for i,g in enumerate(gm):
    if g in go or g in idx: continue
    n+=1
    lc=line_of(i)
    key=lc if lc else ('?',0)
    agg[key]+=1; ex.setdefault(key,(M[i][0],' ; '.join(g)))
print(f'main admin_cto 4-grams absent from the original admin_cto and from all matched windows: {n} of {len(gm)}')
for (ln,col),c in agg.most_common(80):
    s=src[ln-1][max(0,col-1):col+90].strip() if isinstance(ln,int) and ln>0 else ''
    print(f'{c:4d}  admin_cto.rs:{ln}:{col}  {s[:90]}   e.g. @{ex[(ln,col)][0]:#x} {ex[(ln,col)][1][:80]}')
