# gen.py: write EDITS files for s1 clone-at-store source forms (sharing CPI, admin_cto.rs line 749)
import sys,os
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a34-cto-s1clonearray'
D=os.path.dirname(os.path.abspath(__file__))
s=open(WT+'/programs/pump/src/creator/admin_cto.rs').read()
line=[l for l in s.split('\n') if 'admin_cto_sharing_config(' in l][0]
a=line.index('crate::pump_fees::cpi::admin_cto_sharing_config('); b=line.index(',signer_seeds),val)?;')+len(',signer_seeds),val)?;')
OLD=line[a:b]; assert s.count(OLD)==1
T={'pa':'a.pool_authority.to_account_info()','au':'a.admin_set_creator_authority.to_account_info()','gl':'a.global.to_account_info()',
   'mi':'a.mint.to_account_info()','sc':'a.sharing_config.to_account_info()','ev':'a.pump_fees_event_authority.to_account_info()','pr':'a.pump_fees.to_account_info()'}
F=[('pool_authority','pa'),('authority','au'),('global','gl'),('mint','mi'),('sharing_config','sc'),('event_authority','ev'),('program','pr')]
CPI='crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(%s,crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{%s},signer_seeds),val)?;'
lit=','.join(f+':'+T[k] for f,k in F)
short=','.join(f for f,k in F)
V={}
V['s1']=CPI%(T['pr'],lit)
# array literal of the seven struct clones, destructured; CpiContext program clone after / before
V['a7']='let [%s]=[%s];'%(short,','.join(T[k] for f,k in F))+CPI%(T['pr'],short)
V['a7p']='let prog=%s;let [%s]=[%s];'%(T['pr'],short,','.join(T[k] for f,k in F))+CPI%('prog',short)
# eight-element array including the CpiContext program clone first
V['a8']='let [prog,%s]=[%s,%s];'%(short,T['pr'],','.join(T[k] for f,k in F))+CPI%('prog',short)
# tuples
V['t7p']='let prog=%s;let (%s)=(%s);'%(T['pr'],short,','.join(T[k] for f,k in F))+CPI%('prog',short)
V['t8']='let (prog,%s)=(%s,%s);'%(short,T['pr'],','.join(T[k] for f,k in F))+CPI%('prog',short)
# array bound whole, struct fields moved out by destructuring inside the call
V['a7w']='let prog=%s;let accs:[AccountInfo;7]=[%s];let [%s]=accs;'%(T['pr'],','.join(T[k] for f,k in F),short)+CPI%('prog',short)
# struct literal fields as per-field blocks that bind then move (clone bound next to its slot)
V['blk']=CPI%(T['pr'],','.join('%s:{let x=%s;x}'%(f,T[k]) for f,k in F))
for n,new in V.items():
    open(D+'/'+n+'.py','w').write('EDITS=[(%r,%r)]\n'%(OLD,new))
print(' '.join(V))
# Vec push in field order, then moved into the struct through a fixed-size array (keeps the anchor cpi call)
V2={}
V2['vec7p']='let prog=%s;let mut v:Vec<AccountInfo>=Vec::with_capacity(7);%slet [%s]:[AccountInfo;7]=v.try_into().unwrap();'%(T['pr'],''.join('v.push(%s);'%T[k] for f,k in F),short)+CPI%('prog',short)
# array literal whose elements are bound right next to their slot via per-element blocks
V2['a7b']='let prog=%s;let [%s]=[%s];'%(T['pr'],short,','.join('{let x=%s;x}'%T[k] for f,k in F))+CPI%('prog',short)
for n,new in V2.items():
    open(D+'/'+n+'.py','w').write('EDITS=[(%r,%r)]\n'%(OLD,new))
print(' '.join(V2))
