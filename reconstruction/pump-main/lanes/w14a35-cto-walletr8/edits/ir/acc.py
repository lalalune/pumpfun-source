# accounts-pointer reload bound in wallet(): MODE env: blk = fresh load of ctx->accounts per using block (after phis), use = per use
import os,re
MODE=os.environ.get('MODE','blk'); LO=int(os.environ.get('LO','3537')); HI=int(os.environ.get('HI','4172'))
def T(t):
    L=t.split('\n'); out=[]; n=0; blk_has=None
    i=0
    for k,l in enumerate(L):
        ln=k+1
        if LO<=ln<=HI and re.search(r'%_266\b',l) and not l.startswith('  %_266 ='):
            if MODE=='use':
                n+=1; out.append(f'  %acc{n} = load ptr, ptr %2, align 8, !nonnull !2, !align !3, !noundef !2'); l=re.sub(r'%_266\b',f'%acc{n}',l)
            else:
                # find block start in out: last label line
                if blk_has is None:
                    n+=1; j=len(out)
                    while not re.match(r'^[^ ].*:',out[j-1]) : j-=1
                    while j<len(out) and ' = phi ' in out[j]: j+=1
                    out.insert(j,f'  %acc{n} = load ptr, ptr %2, align 8, !nonnull !2, !align !3, !noundef !2'); blk_has=n
                l=re.sub(r'%_266\b',f'%acc{blk_has}',l)
        if re.match(r'^[^ ].*:',l) or l.strip()=='' : blk_has=None
        out.append(l)
    return '\n'.join(out)
EDITS=[T]
