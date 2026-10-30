#!/usr/bin/env python3
"""rx.py <name> [edits.py] [--base raw.ll] [--keep] [--llc args...]  (experiment only; never a source proposal)
Raw-IR opt oracle for 0x22a10 admin_cto::execute. Input: the pre-opt module from tools/capraw.py
(rustc -C no-prepopulate-passes). Applies EDITS (list of exact (old,new) replacements that must each occur
once, or callables text->text), runs the SDK rustlib `opt -O3`, slims the module to execute, runs llc exactly
like fastbuild and scores with target_metric-style tokens (call imm/src and lddw imm masked).
eq_main=true means the tokens equal the current baseline build. Set RX_OUT to choose the scratch dir."""
import sys,os,subprocess,runpy,json,re,time,struct,difflib,glob
H=os.environ.get('HARNESS','/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness')
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
OPT=[p for p in __import__('glob').glob(os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/*/bin/opt'))][0]
