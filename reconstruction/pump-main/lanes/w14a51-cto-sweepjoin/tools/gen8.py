import json,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a33-cto-nativejoin/e/')
VS="  let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&[bump]];vsigner=[vaultseeds];\n"
D0="  let dest=Pubkey::find_program_address("
A0="  let amm_frozen="
VSi=VS.strip()
S={'y1':[[VS,"\n"],[D0,"  "+VSi+"let dest=Pubkey::find_program_address("]],
   'y2':[[VS,"\n"],[A0,"  "+VSi+"let amm_frozen="]],
   'y3':[[VS,"  let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault;let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&[bump]];vsigner=[vaultseeds];\n"],[D0,"  let old=a.current_creator.key();let dest=Pubkey::find_program_address("]]}
for k,v in S.items(): open(O+k+'.py','w').write('EDITS='+json.dumps(v)+'\n')
print(' '.join(S))
