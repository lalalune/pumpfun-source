# unmrefs.py cand.so : for each unmatched window, compare multisets of data lddw targets (section,offset) orig vs best-named candidate symbol
import sys,struct,json,collections,re
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r2-layout-rodata/reconstruction/harness')
from score import candidate_functions, sections, original_windows, score
orig=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r2-layout-rodata/reconstruction/base/original.so','rb').read()
cand=open(sys.argv[1],'rb').read(); os_=sections(orig); cs=sections(cand)
M={0x1e7c0:r'create_v27execute17',0x22a10:r'admin_cto7execute17',0x5b3b0:r'swap_hop17',0x72810:r'sweep7execute17',0x80df8:r'v3_buy_costs17',0x13b9b8:r'buy_v211buy_handler17',0x13f630:r'(buy_exact_quote_in_handler17|buy_exact_quote_in_v217)',0x1489f8:r'(trade15buy_exact_quote17|buy_exact_quote_in_v317)'}
def refs(img,S,st,l):
    t=S['.text']; o=st-t['addr']+t['offset']; c=collections.Counter(); i=0
    while i<l:
        if img[o+i]==0x18:
            v=struct.unpack_from('<I',img,o+i+4)[0]|struct.unpack_from('<I',img,o+i+12)[0]<<32
            for n in ('.rodata','.data.rel.ro','.text'):
                if S[n]['addr']<=v<S[n]['addr']+S[n]['size']: c[(n, v-S[n]['addr'] if n!='.text' else 'fnptr')]+=1
            i+=16
        else: i+=8
    return c
fs=candidate_functions(sys.argv[1]); wl={w['start']:w['bytes'] for w in original_windows()}
for st,rx in M.items():
    f=[x for x in fs if re.search(rx,x[2])]
    if not f: print(hex(st),'no sym'); continue
    a=refs(orig,os_,st,wl[st]); b=refs(cand,cs,f[0][0],f[0][1])
    print(hex(st), f[0][2][16:60], 'orig',sum(a.values()),'cand',sum(b.values()), 'orig-only',dict(a-b),'cand-only',dict(b-a))
