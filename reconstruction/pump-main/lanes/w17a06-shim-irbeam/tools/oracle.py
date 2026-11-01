#!/usr/bin/env python3
"""oracle.py <in.ll|.bc> <name> [--opt "<opt args>"] [--dbg] [--keep] [--so <unstripped.so>] [-- <llc args>]
Lane-local IR/llc oracle for admin_cto::execute (experiment only, never for proposals).
 --opt: run the debug-build opt with these args on the input first (e.g. "-O3 -jump-threading-threshold=0")
 slims the (optimized) module to admin_cto::execute, llc -O3 (SDK v1.44 llc unless --dbg), extracts the
 function from the object, masks call imm/src and lddw imms, and prints ratio/size vs the original window.
"""
import sys,os,re,subprocess,struct,difflib,json,time
L=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w17a06-shim-irbeam')
H='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness'
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
DBG=os.path.expanduser('~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin')
KEEP=r'admin_cto7execute'
def slim(t,keep=KEEP):
    lines=t.split('\n'); res=[]; skip=False
    for l in lines:
        if skip:
            if l=='}': skip=False
            continue
        if l.startswith('define '):
            m=re.match(r'define (.*?)@("[^"]+"|[\w.$]+)\(',l)
            if not re.search(keep,m.group(2)):
                d=l[len('define '):].rstrip()
                assert d.endswith('{'); d=d[:-1].rstrip()
                d=re.sub(r'^(internal|private|linkonce_odr|weak_odr|dso_local|unnamed_addr)\s+','',d)
                d=re.sub(r'^(internal|private|linkonce_odr|weak_odr|dso_local|unnamed_addr)\s+','',d)
                d=re.sub(r'\s+comdat(\([^)]*\))?','',d)
                d=re.sub(r'\s+personality\s+ptr\s+@\S+','',d)
                d=re.sub(r' (%[\w.$"]+)(?=[,)])','',d)
                res.append('declare '+d); skip=True; continue
        if re.match(r'^@\S+ = .*\balias\b',l): continue
        res.append(l)
    return '\n'.join(res)
def elf_fn(path,pat):
    b=open(path,'rb').read()
    shoff=struct.unpack_from('<Q',b,0x28)[0]; shentsize,shnum,shstrndx=struct.unpack_from('<HHH',b,0x3a)
    sh=[struct.unpack_from('<IIQQQQIIQQ',b,shoff+i*shentsize) for i in range(shnum)]
    for i,s in enumerate(sh):
        if s[1]==2:  # SYMTAB
            strtab=sh[s[6]]; so=strtab[4]
            for j in range(s[5]//24):
                nm,info,oth,shndx,val,size=struct.unpack_from('<IBBHQQ',b,s[4]+j*24)
                name=b[so+nm:b.index(b'\0',so+nm)].decode()
                if re.search(pat,name) and (info&0xf)==2:
                    sec=sh[shndx]; off=sec[4]+val-(sec[3] if path.endswith('.so') else 0)
                    return b[off:off+size]
    raise SystemExit('fn not found')
def mask(raw):
    m=bytearray(raw); i=0; toks=[]
    while i<len(raw):
        op=raw[i]; n=16 if op==0x18 else 8
        if op==0x85: m[i+1]&=0x0f; m[i+4:i+8]=b'\0'*4
        if op==0x18: m[i+4:i+8]=b'\0'*4; m[i+12:i+16]=b'\0'*4
        toks.append(bytes(m[i:i+n])); i+=n
    return toks
def orig_window():
    sys.path.insert(0,H)
    from score import original_windows
    for w in original_windows():
        if w['start']==0x22a10: return w['raw']
def metric(cand,orig):
    o=mask(orig); c=mask(cand)
    r=difflib.SequenceMatcher(None,o,c,autojunk=False).ratio()
    ob=b''.join(o); cb=b''.join(c)
    sd=sum(1 for i in range(0,len(ob),8) if ob[i:i+8]!=cb[i:i+8]) if len(ob)==len(cb) else None
    return r,sd
if __name__=='__main__':
    a=sys.argv[1:]; llcargs=[]
    if '--' in a: k=a.index('--'); llcargs=a[k+1:]; a=a[:k]
    src,name=a[0],a[1]; optargs=None; dbg=False; so=None
    i=2
    while i<len(a):
        if a[i]=='--opt': optargs=a[i+1].split(); i+=2
        elif a[i]=='--dbg': dbg=True; i+=1
        elif a[i]=='--so': so=a[i+1]; i+=2
        else: raise SystemExit('bad arg '+a[i])
    d=L+'/irexp/'+name; os.makedirs(d,exist_ok=True); t0=time.time()
    if optargs is not None:
        r=subprocess.run([DBG+'/opt',*optargs,src,'-S','-o',d+'/opt.ll'],capture_output=True,text=True)
        if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
        open(d+'/opt.err','w').write(r.stderr)
        src=d+'/opt.ll'
    t=open(src).read()
    open(d+'/m.ll','w').write(slim(t))
    llc=(DBG if dbg else SDK)+'/llc'
    r=subprocess.run([llc,'-O3','-relocation-model=pic','-mattr=+store-imm,+jmp-ext','-function-sections',d+'/m.ll','-filetype=obj','-o',d+'/m.o',*llcargs],capture_output=True,text=True)
    open(d+'/llc.err','w').write(r.stderr)
    if r.returncode: print(r.stderr[-3000:]); sys.exit(1)
    cand=elf_fn(d+'/m.o',KEEP)
    open(d+'/fn.bin','wb').write(cand)
    orig=orig_window()
    r,sd=metric(cand,orig)
    res={'name':name,'ratio':round(r,5),'bytes':len(cand),'slots_diff':sd,'secs':round(time.time()-t0,1)}
    if so:
        base=elf_fn(so,KEEP); res['eq_so']=mask(base)==mask(cand)
    print(json.dumps(res))
    open(d+'/res.json','w').write(json.dumps(res))
