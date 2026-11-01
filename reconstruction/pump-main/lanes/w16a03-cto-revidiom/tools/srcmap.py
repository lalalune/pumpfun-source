"""srcmap: original window address -> source location of the same instruction in the line-table build.
Uses the window's symbol (score.json), the asm function body (asmlines.py), instruction index alignment and a mnemonic check."""
import sys,os,pickle,bisect,re
sys.path.insert(0,os.path.dirname(__file__))
import shape
OUT=shape.OUT
_files,_funcs=pickle.load(open(OUT+'/lines/asm.pkl','rb'))
_o=shape.orig(); _addr=[a for a,t,p in _o]
def win_insns(w):
    i=bisect.bisect_left(_addr,w[0]); out=[]
    while i<len(_o) and _o[i][0]<w[0]+w[1]: out.append(_o[i]); i+=1
    return out
def fn_for(w):
    for s in w[2]:
        if s in _funcs: return s
    return None
_cache={}
def _norm(t):
    t=t.split()[0]
    return t
def loc(addr):
    w=shape.win_of(addr)
    if not w: return None
    key=w[0]
    if key not in _cache:
        f=fn_for(w)
        if f is None and w[0]==0x22a10: f=[k for k in _funcs if 'admin_cto7execute' in k][0]
        _cache[key]=(f,win_insns(w))
    f,ins=_cache[key][:2]
    if f is None: return ('?',None,None,'no asm fn')
    body=_funcs[f]
    if len(_cache[key])==2:
        import difflib
        A=[_norm(t) for _,t,_ in ins]; B=[_norm(s) for s,l in body]
        mp={}
        if A==B: mp={i:i for i in range(len(A))}
        else:
            for tag,i1,i2,j1,j2 in difflib.SequenceMatcher(None,A,B,autojunk=False).get_opcodes():
                if tag=='equal':
                    for k in range(i2-i1): mp[i1+k]=j1+k
        _cache[key]=(f,ins,mp)
    mp=_cache[key][2]
    addrs=[a for a,t,p in ins]
    if addr not in addrs: return (f,None,None,'idx')
    idx=addrs.index(addr)
    exact=idx in mp; j=mp.get(idx)
    if j is None:
        # nearest mapped neighbour before
        k=idx
        while k>=0 and k not in mp: k-=1
        j=mp.get(k)
    if j is None: return (f,None,None,'unmapped')
    s,l=body[j]
    if l is None: return (f,None,None,'noloc')
    return (f,_files.get(l[0],str(l[0])),l[1],l[2],'ok' if exact else 'approx')
if __name__=='__main__':
    from win_dm import dm
    for x in sys.argv[1:]:
        a=int(x,16)
        r=loc(a); print(hex(a), r if r is None else (dm(r[0])[:80],)+tuple(r[1:]))

_userfiles=None
def userloc(addr):
    """nearest asm instruction at or before the mapped one whose .loc is in programs/ (the user call site of inlined code)"""
    global _userfiles
    if _userfiles is None: _userfiles={k for k,v in _files.items() if v.startswith('programs/')}
    r=loc(addr)
    if r is None or r[1] is None: return None
    w=shape.win_of(addr); f,ins,mp=_cache[w[0]]
    addrs=[a for a,t,p in ins]; idx=addrs.index(addr)
    k=idx
    while k>=0 and k not in mp: k-=1
    if k<0: return None
    j=mp[k]; body=_funcs[f]
    while j>=0:
        l=body[j][1]
        if l and l[0] in _userfiles: return (_files[l[0]],l[1],l[2])
        j-=1
    return None
_srccache={}
def srcline(path,line,root='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a03-cto-revidiom/'):
    if path not in _srccache:
        try: _srccache[path]=open(root+path).read().split('\n')
        except Exception: _srccache[path]=[]
    L=_srccache[path]
    return L[line-1] if 0<line<=len(L) else ''
