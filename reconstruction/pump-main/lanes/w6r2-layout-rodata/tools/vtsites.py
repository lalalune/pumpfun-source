import sys,struct,re
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r2-layout-rodata/reconstruction/harness')
from score import candidate_functions, sections
orig=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w6r2-layout-rodata/reconstruction/base/original.so','rb').read()
def scan(img,st,l,sec,off):
    S=sections(img); t=S['.text']; o=st-t['addr']+t['offset']; code=img[o:o+l]; res=[]; i=0
    while i<l:
        if code[i]==0x18:
            v=struct.unpack_from('<I',code,i+4)[0]|struct.unpack_from('<I',code,i+12)[0]<<32
            if v==S[sec]['addr']+off:
                # context: nearest line immediates within +-0x100 and calls
                ctx=[]
                for j in range(i,min(l,i+0x400),8):
                    op=code[j]; imm=struct.unpack_from('<i',code,j+4)[0]
                    if op in (0x62,0x7a,0xb7) and 280<=imm<=770: ctx.append(('L',hex(j),imm))
                    if op==0x85: ctx.append(('call',hex(j)))
                res.append((hex(i),ctx[:6]))
            i+=16
        else: i+=8
    return res
sec,off=sys.argv[2],int(sys.argv[3],16)
print('ORIG'); [print(' ',x) for x in scan(orig,0x22a10,27400,sec,off)]
for st,l,n in candidate_functions(sys.argv[1]):
    if re.search('admin_cto7execute17',n):
        print('CAND'); [print(' ',x) for x in scan(open(sys.argv[1],'rb').read(),st,l,sec,off)]; break
b=orig; S=sections(b)['.data.rel.ro']; d=b[S['offset']+off:S['offset']+off+24]; print('vtable words',[hex(struct.unpack_from('<Q',d,k)[0]) for k in (0,8,16)])
