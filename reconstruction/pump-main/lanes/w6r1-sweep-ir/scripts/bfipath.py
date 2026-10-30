import re,subprocess,sys
nl=open(sys.argv[1]).read()
r=subprocess.run(['/Users/shawwalters/.rustup/toolchains/solana/lib/rustlib/aarch64-apple-darwin/bin/opt','-disable-output','-passes=print<block-freq>',sys.argv[1]],capture_output=True,text=True)
freq={m.group(1):float(m.group(2)) for m in re.finditer(r' - (\S+): float = (\S+),',r.stderr)}
cur=None; calls={}
for l in nl.splitlines():
    m=re.match(r'^(\S+):',l)
    if m: cur=m.group(1); calls[cur]=[]; continue
    c=re.search(r'call .*?@([\w.$"]+)\(',l)
    if c and cur and not c.group(1).startswith('llvm.'): calls[cur].append(re.sub(r'_ZN\d+|17h[0-9a-f]+E|\$LT\$|\$GT\$|\$u20\$','',c.group(1))[:40])
    if re.match(r'\s+(br|switch|ret|unreachable)',l):
        print(f'{freq.get(cur,0):8.5f} {cur:8s} {l.strip()[:90]:90s} {",".join(calls[cur])[:80]}')
