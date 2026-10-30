#!/bin/bash
# bfix.sh <var> : execute-context frequency of every to_string site (all to_string noinline; BFI after execute's inliner)
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a43-cto-outline306; v=$1; w=${2:-work0}
OPT=~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/aarch64-apple-darwin/bin/opt; D=$O/ir/b_$v; mkdir -p $D
[ -f $O/ir/$v/pump_recovered.raw.ll ] && ln -sf $O/ir/$v/pump_recovered.raw.ll $D/pump_recovered.raw.ll; [ -f $D/pump_recovered.raw.ll ] || python3 $O/tools/capraw.py $O/var/$v $O/$w $D > $D.log 2>&1
python3 - $D <<'PY'
import sys,re
D=sys.argv[1]; t=open(D+'/pump_recovered.raw.ll').read()
k=t.index('define internal void @"_ZN45_$LT$T$u20$as$u20$alloc..string..ToString$GT$9to_string17h1551814bef63e52cE"')
e=t.index('\n',k); line=t[k:e]; n=re.search(r'unnamed_addr #(\d+) \{',line).group(1)
attr=re.search(r'^attributes #'+n+r' = \{ (.*) \}$',t,re.M).group(1).replace('inlinehint ','')
t=t[:k]+line.replace('unnamed_addr #'+n+' {','unnamed_addr #991 {')+t[e:]+'\nattributes #991 = { noinline '+attr+' }\n'
open(D+'/ni.ll','w').write(t)
PY
E=$(grep -o "^define[^@]*@_ZN14pump_recovered9admin_cto7execute[A-Za-z0-9_]*" $D/pump_recovered.raw.ll | sed "s/.*@//" | head -1)
$OPT -O3 -print-after=inline -print-module-scope -filter-print-funcs=$E $D/ni.ll -o /dev/null 2> $D/post.txt
python3 - $D $E <<'PY'
import sys
D,E=sys.argv[1:3]; t=open(D+'/post.txt').read(); hs=[i for i in range(len(t)) if t.startswith('; *** IR Dump After InlinerPass',i)] if False else None
k=t.rfind('; *** IR Dump After'); body=t[t.index('\n',k)+1:]
open(D+'/post.ll','w').write(body)
PY
$OPT -passes='print<block-freq>' -disable-output $D/post.ll 2> $D/bfx_all.txt
python3 - $D $E <<'PY'
import sys,re
D,E=sys.argv[1:3]; t=open(D+'/bfx_all.txt').read(); i=t.find("block-frequency-info: "+E); j=t.find("block-frequency-info:",i+10); bf=t[i:j]
F={m.group(1):float(m.group(2)) for m in re.finditer(r'- (\S+): float = ([\d.e+-]+)',bf)}
L=open(D+'/post.ll').read().split('\n'); s=next(k for k,l in enumerate(L) if l.startswith('define') and E in l); e=next(k for k in range(s,len(L)) if L[k]=='}')
blk='start'; out=[]
for k in range(s,e):
    l=L[k]; m=re.match(r'^([\w.\-]+):',l)
    if m: blk=m.group(1)
    if 'ToString$GT$9to_string' in l and 'call' in l:
        ln=None
        for q in range(k,min(e,k+200)):
            mm=re.search(r'store i32 (\d{3}),',L[q])
            if mm and 280<=int(mm.group(1))<=800: ln=mm.group(1); break
        out.append((ln,round(F.get(blk,-1),5)))
print(' '.join(f'{a}:{b}{"C" if b<0.02 else ""}' for a,b in out))
PY
rm -f $D/post.txt $D/bfx_all.txt $D/ni.ll
