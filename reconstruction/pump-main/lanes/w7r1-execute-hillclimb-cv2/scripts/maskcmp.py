import sys,subprocess,re,difflib,os
SDK=os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
sys.path.insert(0,os.path.dirname(__file__)); import ir
def fn(so):
    sy=subprocess.check_output([SDK+'/llvm-readelf','-sW',so],text=True)
    for l in sy.splitlines():
        f=l.split()
        if len(f)>=8 and re.search(r'create_v27execute',f[7]): a=int(f[1],16); n=int(f[2]); break
    return ir.norm(subprocess.check_output([SDK+'/llvm-objdump','-d','--no-show-raw-insn','--start-address=%#x'%a,'--stop-address=%#x'%(a+n),so],text=True))
def mask(L): return [re.sub(r'r10 - 0x[0-9a-f]+','r10-X',re.sub(r'add64 (r\d), -0x[0-9a-f]+',r'add64 \1, -X',x)) for x in L]
o=mask(ir.orig())
for so in sys.argv[1:]:
    c=mask(fn(so)); sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
    d=[l for l in difflib.unified_diff(o,c,n=0,lineterm='') if l[:1] in '+-' and l[:3] not in ('+++','---')]
    print(so.split('/')[-2],len(c),len(d),round(sm.ratio(),5))
    if os.environ.get('V'): print('\n'.join(d[:60]))
