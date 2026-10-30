import json,os
OUT=os.path.dirname(os.path.abspath(__file__))
O='let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[bump]];vsigner=[vaultseeds];'
V={
'vs_inline':'let vsigner:[&[&[u8]];1];let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[ctx.bumps.creator_vault]];vsigner=[vaultseeds];',
'vs_arr':'let vsigner:[&[&[u8]];1];let bump=[ctx.bumps.creator_vault];let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&bump];vsigner=[vaultseeds];',
'vs_let':'let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[bump]];let vsigner=[vaultseeds];',
'vs_oldfirst':'let vsigner:[&[&[u8]];1];let old=a.current_creator.key();let bump=ctx.bumps.creator_vault;let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[bump]];vsigner=[vaultseeds];',
'vs_olda':'let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",AsRef::<[u8]>::as_ref(&old),&[bump]];vsigner=[vaultseeds];',
'vs_bytes':'let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[&b"creator-vault"[..],old.as_ref(),&[bump]];vsigner=[vaultseeds];',
'vs_slice1':'let vsigner:&[&[&[u8]]];let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[bump]];vsigner=&[vaultseeds];',
}
for n,new in V.items(): open(f'{OUT}/{n}.py','w').write('EDITS='+json.dumps([(O,new)])+'\n')
print(' '.join(V))
