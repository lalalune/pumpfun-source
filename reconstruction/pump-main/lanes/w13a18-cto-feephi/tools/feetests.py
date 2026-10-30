#!/usr/bin/env python3
"""feetests.py <rxdir>: post-opt execute CFG around the fee-tag tests (fee tag = 3rd arg).
Prints each fee-tag test block, its preds, None successor (preds count, #non-phi insts, terminator)."""
import sys,re
d=sys.argv[1]; t=open(d+'/o3.ll').read()
s=t.index('admin_cto7execute'); s=t.rfind('\ndefine',0,s); e=t.index('\n}\n',s); body=t[s:e]
hdr=body.split('\n',2)[1]
args=re.findall(r'(i8|i64|ptr)[^,%]*?(%[\w.]+)[,)]',hdr)
tag=args[2][1]
blocks={};order=[];cur=None
for l in body.split('\n')[2:]:
    m=re.match(r'^([\w.\-$"]+):(.*)',l)
    if m: cur=m.group(1); order.append(cur); blocks[cur]={'pre':m.group(2),'ins':[]}; continue
    if cur and l.strip(): blocks[cur]['ins'].append(l.strip())
preds={b:[] for b in blocks}
for b in order:
    term=blocks[b]['ins'][-1]
    for x in re.findall(r'label %([\w.\-$"]+)',term): preds.setdefault(x.strip('"'),[]).append(b)
feecmp=set()
for b in order:
    for i in blocks[b]['ins']:
        m=re.match(r'(%[\w.]+) = icmp (eq|ne) i64 '+re.escape(tag)+r', 0',i)
        if m: feecmp.add((m.group(1),m.group(2)))
def desc(b):
    ins=blocks[b]['ins']; np=[i for i in ins if ' = phi ' not in i and 'lifetime' not in i]
    return f"{b}[preds={len(preds.get(b,[]))},n={len(np)}] -> {ins[-1][:110]}"
print('fee tag',tag,'tests:',len(feecmp))
for b in order:
    term=blocks[b]['ins'][-1]
    for v,k in feecmp:
        if term.startswith('br i1 '+v+','):
            L=re.findall(r'label %([\w.\-$"]+)',term); none=L[0] if k=='eq' else L[1]; some=L[1] if k=='eq' else L[0]
            print(f"TEST {b} preds={preds.get(b)}\n   None-> {desc(none)}\n   Some-> {desc(some)}")
