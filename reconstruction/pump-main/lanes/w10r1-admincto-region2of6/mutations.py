# mut.py IN OUT [set...] : apply named mutation sets
import sys
s=open(sys.argv[1]).read()
M={
'tree':[('let sharing_update=if shared{Some(if holder{None}else{new})}else{None};let collect_old=sharing_update.is_none()&&!st.holder_reward&&st.creator!=Pubkey::default();if shared&&!holder{target=st.creator;}(holder,cashback,target,sharing_update,collect_old)};',
 'let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(new),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};(holder,cashback,target,sharing_update,collect_old,skip)};'),
 ('let (holder,cashback,target,sharing_update,collect_old)={','let (holder,cashback,target,sharing_update,collect_old,skip)={'),
 ('if shared && holder{swept=','if !skip{swept=')],
'feematch':[(' if let Some(f)=fee{if st.quote_locked{',' match fee{None=>{},Some(f)=>{if st.quote_locked{'),('return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}','return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}}')],
'oldbump':[('let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();','let old=a.current_creator.key();let bump=[ctx.bumps.creator_vault];')],
'vsigner':[('let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&bump];','let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&bump];let vsigner:&[&[&[u8]];1]=&[vaultseeds];'),('amount,&[vaultseeds])?;}amount}','amount,vsigner)?;}amount}'),('amount,&[vaultseeds])?;}','amount,vsigner)?;}')],
}
for k in sys.argv[3:]:
    for o,n in M[k]:
        c=s.count(o)
        if c!=1: sys.exit(f'{k}: count {c} for {o[:50]!r}')
        s=s.replace(o,n)
open(sys.argv[2],'w').write(s)
