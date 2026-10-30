import sys,re
# cfg.py <fn.ll> [lo hi]: block label, #insts, phis, notable lines, terminator
L=open(sys.argv[1]).read().split('\n')
lo=int(sys.argv[2]) if len(sys.argv)>2 else 0; hi=int(sys.argv[3]) if len(sys.argv)>3 else 10**9
cur=None;n=0;notes=[]
for i,l in enumerate(L,1):
    m=re.match(r'^([\w.\-]+):',l)
    if m:
        cur=m.group(1);n=0;notes=[];start=i;continue
    if cur is None: continue
    s=l.strip()
    if not s or s.startswith(';'): continue
    n+=1
    if ' phi ' in s: notes.append(s.split('=')[0].strip()+'=phi['+','.join(re.findall(r'\[ ?([^,]+),',s))[:60]+']')
    mm=re.search(r'store i32 (\d+), ptr %\S*line',s)
    if re.search(r'store i32 (2[89]\d|3[0-4]\d|410)\b',s): notes.append('L'+re.search(r'store i32 (\d+)',s).group(1))
    if s.startswith(('br ','switch ','ret ','unreachable','resume')) or s.startswith('i64 ') or s.startswith(']'):
        if s.startswith(('br','switch','ret','unreachable')) and lo<=start<=hi:
            t=s if not s.startswith('switch') else s
            print(f'{start:5d} {cur:28s} n={n:3d} {" ".join(notes)[:150]} || {t[:160]}')
