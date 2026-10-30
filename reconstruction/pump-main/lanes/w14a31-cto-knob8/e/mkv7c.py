import os,json,sys
OUT=os.path.dirname(os.path.abspath(__file__))
src=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a31-cto-knob8/programs/pump/src/creator/admin_cto.rs').read()
VL='fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);'
_i=src.index(VL); _j=src.index(' Ok(target)}pub fn execute(')
VBODY=src[_i+len(VL):_j]
CALL='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
_k=src.index(CALL)
EX_HEAD=src[_j+len(' Ok(target)}'):_k]
old=src[_i:_k+len(CALL)]
new=EX_HEAD+'let mut target=(||->Result<Pubkey>{let st=&st;let holder_key=&holder_key;let sharing=&sk;let holder=hopt==Some(true);'+VBODY+' Ok(target)})()?;'
assert old.count('\n')==new.count('\n')
V7C=[(old,new)]
if __name__=='__main__':
    open(OUT+'/v7c.py','w').write('EDITS='+json.dumps(V7C)+'\n')
    # pairs: v7c + each knob in argv
    for n in sys.argv[1:]:
        g={};exec(open(f'{OUT}/{n}.py').read(),g)
        open(f'{OUT}/v7c_{n}.py','w').write('EDITS='+json.dumps(V7C+[tuple(x) for x in g['EDITS']])+'\n')
