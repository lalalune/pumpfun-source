import json,os
OUT=os.path.dirname(os.path.abspath(__file__))
O="if native{let rent=Rent::get()?;let min=rent.minimum_balance(0);let amount=a.creator_vault.lamports().saturating_sub(min);"
V={
'r_minvar':[(O,"if native{let rent=Rent::get()?;let amount=a.creator_vault.lamports().saturating_sub(rent.minimum_balance(0));")],
'r_inline':[(O,"if native{let amount=a.creator_vault.lamports().saturating_sub(Rent::get()?.minimum_balance(0));")],
'r_map':[(O,"if native{let min=Rent::get().map(|r|r.minimum_balance(0))?;let amount=a.creator_vault.lamports().saturating_sub(min);")],
'r_ref':[(O,"if native{let rent=&Rent::get()?;let min=rent.minimum_balance(0);let amount=a.creator_vault.lamports().saturating_sub(min);")],
'r_lamfirst':[(O,"if native{let lam=a.creator_vault.lamports();let min=Rent::get()?.minimum_balance(0);let amount=lam.saturating_sub(min);")],
'r_lamfirst2':[(O,"if native{let lam=a.creator_vault.lamports();let rent=Rent::get()?;let min=rent.minimum_balance(0);let amount=lam.saturating_sub(min);")],
'r_minexempt':[(O,"if native{let min=Rent::get()?.minimum_balance(0usize);let amount=a.creator_vault.lamports().saturating_sub(min);")],
}
for n,e in V.items(): open(f'{OUT}/{n}.py','w').write('EDITS='+json.dumps(e)+'\n')
print(' '.join(V))
