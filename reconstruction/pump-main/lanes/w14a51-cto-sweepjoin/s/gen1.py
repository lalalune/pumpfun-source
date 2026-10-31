import json,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a51-cto-sweepjoin/s/')
VS='  let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[bump]];vsigner=[vaultseeds];\n'
D0='  let dest=Pubkey::find_program_address('
IF0='.0;if a.holder_creator_vault.key()!=dest{'
VSd='  let bump=ctx.bumps.creator_vault;old=a.current_creator.key();bb=[bump];sa=[b"creator-vault",old.as_ref(),&bb];let vaultseeds:&[&[u8]]=&sa;vsigner=[vaultseeds];\n'
DEC='let vsigner:[&[&[u8]];1];let old:Pubkey;let bb:[u8;1];let sa:[&[u8];3];'
DEC2='let sa:[&[u8];3];let bb:[u8;1];let old:Pubkey;let vsigner:[&[&[u8]];1];'
S={
 'd1':[[VS,VSd],[D0,'  '+DEC+'let dest=Pubkey::find_program_address(']],
 'd2':[[VS,VSd],[IF0,'.0;'+DEC+'if a.holder_creator_vault.key()!=dest{']],
 'd3':[[VS,VSd],[D0,'  '+DEC2+'let dest=Pubkey::find_program_address(']],
 # named locals in place (no early decl): isolates the named-array effect
 'd0':[[VS,'  let vsigner:[&[&[u8]];1];let old:Pubkey;let bb:[u8;1];let sa:[&[u8];3];'+VSd.strip()+'\n']],
}
for k,v in S.items(): open(O+k+'.py','w').write('EDITS='+json.dumps(v)+'\n')
print(' '.join(S))
