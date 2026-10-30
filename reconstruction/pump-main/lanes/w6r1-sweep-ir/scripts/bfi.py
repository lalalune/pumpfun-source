import re,sys,subprocess
# bfi.py build.log -> run homebrew opt print<block-freq> on the first dumped function
t=open(sys.argv[1]).read()
i=t.index('; *** IR Dump Before InlinerPass'); f=t[i:]; f=f[f.index('define'):]; f=f[:f.index('\n}\n')+3]
f=re.sub(r' #\d+',' ',f); f=re.sub(r'@(\d+)\b',r'@g\1',f); f=re.sub(r', !(dbg|noalias|alias\.scope|range|noundef|nonnull|align|prof|tbaa|annotation) ![0-9]+','',f)
f=re.sub(r'!(noundef|nonnull) !\{\}','',f)
f=re.sub(r'\n\s*call void @llvm.experimental.noalias.scope.decl\(metadata ![0-9]+\)','',f)
f=re.sub(r', !\w+ ![0-9]+','',f)
names=set(re.findall(r'@("[^"]+"|[\w.$]+)',f)); me=re.search(r'@(\S+?)\(',f).group(1); names.discard(me)
decls=[]
for n in names:
    if re.search(r'call [^@]*@'+re.escape(n)+r'\(',f) or re.search(r'invoke [^@]*@'+re.escape(n)+r'\(',f):
        if n.startswith('llvm.'):
            m=re.search(r'call ([^@]*?) @'+re.escape(n)+r'\(',f)
            continue
        decls.append(f'declare void @{n}()')
    else: decls.append(f'@{n} = external global i8')
src='\n'.join(decls)+'\n'+f
open(sys.argv[2],'w').write(src)
r=subprocess.run(['/Users/shawwalters/.rustup/toolchains/solana/lib/rustlib/aarch64-apple-darwin/bin/opt','-S','-passes=instnamer',sys.argv[2],'-o',sys.argv[2]+'.n.ll'],capture_output=True,text=True)
if r.returncode: print(r.stderr); sys.exit(1)
r=subprocess.run(['/Users/shawwalters/.rustup/toolchains/solana/lib/rustlib/aarch64-apple-darwin/bin/opt','-disable-output','-passes=print<block-freq>',sys.argv[2]+'.n.ll'],capture_output=True,text=True)
freq={}
for l in r.stderr.splitlines():
    m=re.match(r' - (\S+): float = (\S+),',l)
    if m: freq[m.group(1)]=float(m.group(2))
nl=open(sys.argv[2]+'.n.ll').read()
cur=None
for l in nl.splitlines():
    m=re.match(r'^(\S+):',l)
    if m: cur=m.group(1)
    c=re.search(r'call .*?@([\w.$"]+)\(',l)
    if c and cur and not c.group(1).startswith('llvm.'):
        print(f'{freq.get(cur,-1):9.5f} {cur:10s} {c.group(1)[:110]}')

