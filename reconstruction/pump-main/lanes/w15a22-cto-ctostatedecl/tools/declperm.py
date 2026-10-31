"""declperm.py: IR-level emulation of a CtoState bool DECLARATION order (experiment only).
repr(Rust) keeps declaration order among the six align-1 bools (offsets 40..45 after creator[0..32) and max_fee[32..40)),
and rustc's Aggregate codegen stores fields in declaration order. ORDER env = comma list of the 6 bool names in
declaration order. Rewrites every `gep i8, ptr %st, i64 40..45` in execute and validate, fixes the align of the
dependent load/store, and reorders the aggregate's bool stores into declaration order."""
import os,re
BOOLS=['mayhem','holder_reward','cashback','quote_locked','holder_enabled','fee_configurable']
def al(o):
    a=1
    while a<8 and o%(a*2)==0: a*=2
    return a
def make(order):
    old={b:40+i for i,b in enumerate(BOOLS)}; new={b:40+order.index(b) for b in BOOLS}
    m={old[b]:new[b] for b in BOOLS}
    def ed(t):
        out=[]; pos=0
        for fn in (r'admin_cto8validate',r'admin_cto7execute'):
            k=re.search(r'\ndefine [^\n]*'+fn+r'17h',t).start(); e=t.index('\n}\n',k)
            b=t[k:e]; gmap={}
            def g(mo):
                gmap[mo.group(1)]=m[int(mo.group(2))]; return f'{mo.group(1)} = getelementptr inbounds i8, ptr %st, i64 {m[int(mo.group(2))]}'
            b=re.sub(r'(%[\w.]+) = getelementptr inbounds i8, ptr %st, i64 (4[0-5])\b',g,b)
            def fa(mo):
                v=mo.group(2)
                if v in gmap: return mo.group(1)+v+', align '+str(al(gmap[v]))
                return mo.group(0)
            b=re.sub(r'((?:load i8, ptr |store i8 %[\w.]+, ptr ))(%[\w.]+), align \d+',fa,b)
            if fn=='admin_cto7execute':
                # reorder the aggregate's 6 bool store triples (they follow the max_fee store) into declaration order
                mo=re.search(r'(  %[\w.]+ = getelementptr inbounds i8, ptr %st, i64 32\n  store i64 [^\n]+\n)((?:  %[\w.]+ = getelementptr inbounds i8, ptr %st, i64 4[0-5]\n  %[\w.]+ = zext i1 [^\n]+\n  store i8 [^\n]+\n){6})',b)
                assert mo,'aggregate not found'
                tr=re.findall(r'  %[\w.]+ = getelementptr inbounds i8, ptr %st, i64 (4[0-5])\n  %[\w.]+ = zext i1 [^\n]+\n  store i8 [^\n]+\n',mo.group(2))
                R=r'  (%[\w.]+) = getelementptr inbounds i8, ptr %st, i64 (4[0-5])\n  (%[\w.]+) = zext i1 ([^\n]+) to i8\n  store i8 %[\w.]+, ptr %[\w.]+, align \d+\n'
                trs=re.findall(R,mo.group(2)); assert len(trs)==6
                src=sorted(trs,key=lambda x:int(x[1]))
                trs=''.join(f'  {trs[j][0]} = getelementptr inbounds i8, ptr %st, i64 {src[j][1]}\n  {trs[j][2]} = zext i1 {src[j][3]} to i8\n  store i8 {trs[j][2]}, ptr {trs[j][0]}, align {al(int(src[j][1]))}\n' for j in range(6))
                b=b[:mo.start(2)]+''.join(trs)+b[mo.end(2):]
            t=t[:k]+b+t[e:]
        return t
    return ed
EDITS=[make(os.environ['ORDER'].split(','))]
