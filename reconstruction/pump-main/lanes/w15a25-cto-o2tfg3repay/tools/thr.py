#!/usr/bin/env python3
"""thr.py <raw.ll> [edits.py]: per-error-site inline threshold of validate's to_string calls in the REAL -O3 pipeline.
Each to_string call site in validate is redirected to an external-linkage clone named by its PumpError code, then opt -O3
-pass-remarks{,-missed}=inline reports (cost, threshold) per site: threshold 45 = cold-callsite rule (outlined)."""
import sys,re,os,subprocess,runpy,glob,tempfile
OPT=glob.glob(os.path.expanduser('~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/*/bin/opt'))[0]
CODE2LINE={88:284,83:289,84:296,90:298,89:306,30:307,19:312,91:326,80:330,78:334,77:338}
def clone(t):
    i=t.index(re.search(r'define [^\n]*admin_cto8validate',t).group(0)); j=t.index('\n}\n',i)
    L=t[i:j].split('\n'); code=None; codes=[]
    TS='_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h1551814bef63e52cE'
    for k,l in enumerate(L):
        m=re.search(r'for\$u20\$u32\$GT\$4from\S*\(i32 noundef (\d+)\)',l)
        if m: code=int(m.group(1))
        if TS in l and 'call' in l:
            L[k]=l.replace('@"'+TS+'"',f'@"TS_{code}"'); codes.append(code)
    t=t[:i]+'\n'.join(L)+t[j:]
    m=re.search(r'\ndefine internal void @"'+re.escape(TS)+r'"[^\n]*\{\n.*?\n\}\n',t,re.S)
    body=m.group(0)
    for c in codes:
        t+=body.replace('define internal void @"'+TS+'"',f'define void @"TS_{c}"')
    return t,codes
if __name__=='__main__':
    t=open(sys.argv[1]).read()
    if len(sys.argv)>2:
        for e in runpy.run_path(sys.argv[2])['EDITS']:
            if callable(e): t=e(t); continue
            x,y=e; assert t.count(x)==1; t=t.replace(x,y)
    t,codes=clone(t)
    fd,p=tempfile.mkstemp(suffix='.ll'); os.write(fd,t.encode()); os.close(fd)
    r=subprocess.run([OPT,'-O3',p,'-o','/dev/null','-pass-remarks=inline','-pass-remarks-missed=inline'],capture_output=True,text=True); os.remove(p)
    res={}
    for l in r.stderr.split('\n'):
        m=re.search(r"'TS_(\d+)' (inlined|not inlined) into '(\S+)'.*?cost=(-?\d+), threshold=(-?\d+)",l)
        if m:
            c=int(m.group(1)); who='V' if 'validate' in m.group(3) else 'E' if '7execute' in m.group(3) else m.group(3)[:30]
            res.setdefault(c,[]).append(f"{who}:{'I' if m.group(2)=='inlined' else 'O'}{m.group(4)}/{m.group(5)}")
    print(' '.join(f"{CODE2LINE.get(c,c)}[{','.join(res.get(c,['?']))}]" for c in codes))
