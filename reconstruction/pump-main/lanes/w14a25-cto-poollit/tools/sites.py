#!/usr/bin/env python3
"""sites.py <so|o> : per-site table of the admin_cto tail. Alignment = sk SequenceMatcher (orig vs cand);
per site: orig insns, cand insns, matched sk / fm / raw (raw: call+jump imm masked, as ch3)."""
import sys,os,difflib,re,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import absratio as A, amap
SITES=[('sharing CPI ret + curve update + pool gate',0x49f8,0x4c10),('pool CPI clone run + admin_cto_pool call',0x4c10,0x4df0),
('post-pool Clock + AdminCtoEvent build + emit!',0x4df0,0x50c0),('AdminCtoEvent emit_cpi (clone, data, ix, invoke_signed)',0x50c0,0x5388),
('emit_cpi Err/drop + error tails (to_string, AnchorError)',0x5388,0x5990),('sweep native arm (Rent, ensure_rent_exempt, transfer)',0x5990,0x5bd0),
('wallet gates (native, data_is_empty, token_frozen)',0x5bd0,0x5cd0),('wallet ATA create #1 clone run + call',0x5cd0,0x5e40),
('ATA create #2 clone run + call',0x5e40,0x6000),('transfer_vault_tokens + collect + Clock',0x6000,0x62c0),
('collect Ok/Err joins + do_coin token_frozen',0x62c0,0x63a0),('CollectCreatorFeeEvent build + emit!',0x63a0,0x64d8),
('collect emit_cpi (authority clone, data, ix, invoke_signed)',0x64d8,0x6798),('emit_cpi drops + coin gate',0x6798,0x6878),
('collect_coin_creator_fee clone run + call',0x6878,0x6a28),('coin CPI Err joins + drops',0x6a28,0x7000)]
def CRn(s):
    s=re.sub(r'\s+<[^>]*>','',s.strip())
    if s.startswith('call'): return 'call'
    s=re.sub(r'^lddw (r\d+), .*',r'lddw \1',s)
    if s.startswith('j'): s=re.sub(r'[+-]0x[0-9a-f]+$|[+-]\d+$','J',s)
    return s
def table(p,base=None):
    C=amap.lines(p); OL=amap.OL
    a=[A.norm(x[1],True) for x in OL]; b=[A.norm(x[1],True) for x in C]
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    res={s[0]:dict(o=0,c=0,sk=0,fm=0,raw=0,olo=None,ohi=None) for s in SITES}
    def site(off):
        for s in SITES:
            if s[1]<=off<s[2]: return s[0]
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            i=blk.a+k; j=blk.b+k; s=site(int(C[j][0],16))
            if not s: continue
            r=res[s]; r['sk']+=1
            if A.norm(OL[i][1],False)==A.norm(C[j][1],False): r['fm']+=1
            if CRn(OL[i][1])==CRn(C[j][1]): r['raw']+=1
            oo=int(OL[i][0],16); r['olo']=oo if r['olo'] is None else min(r['olo'],oo); r['ohi']=oo if r['ohi'] is None else max(r['ohi'],oo)
    for x in C:
        s=site(int(x[0],16))
        if s: res[s]['c']+=1
    for s in SITES:
        r=res[s[0]]
        if r['olo'] is not None: r['o']=sum(1 for x in OL if r['olo']<=int(x[0],16)<=r['ohi'])
    return res
if __name__=='__main__':
    R=[table(p) for p in sys.argv[1:]]
    print('| site | ours | orig | orig n | ours n | sk | fm | raw |' + ''.join(f' d{k} |' for k in range(1,len(R))))
    print('|---|---|---|--:|--:|--:|--:|--:|' + '--|'*(len(R)-1))
    for s in SITES:
        r=R[0][s[0]]
        extra=''.join(f" {R[k][s[0]]['sk']-r['sk']:+d}/{R[k][s[0]]['fm']-r['fm']:+d}/{R[k][s[0]]['raw']-r['raw']:+d} |" for k in range(1,len(R)))
        print(f"| {s[0]} | {s[1]:#x}-{s[2]:#x} | {r['olo'] or 0:#x}-{r['ohi'] or 0:#x} | {r['o']} | {r['c']} | {r['sk']} | {r['fm']} | {r['raw']} |"+extra)
