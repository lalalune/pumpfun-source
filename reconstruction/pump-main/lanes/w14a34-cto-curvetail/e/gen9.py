import os
D=os.path.dirname(os.path.abspath(__file__))+'/e'
A=" match sharing_update{Some(val)=>{\n"; B="\n }None=>{}}\n"; V="signer_seeds),val)?;"
X={
 'm_nonefirst':[(A," match sharing_update{None=>{}Some(val)=>{\n"),(B,"\n }}\n")],
 'm_iflet_else':[(A," if let Some(val)=sharing_update{\n"),(B,"\n }else{}\n")],
 'm_iflet_ref':[(A," if let Some(val)=&sharing_update{\n"),(B,"\n }\n"),(V,"signer_seeds),*val)?;")],
 'm_iflet_copied':[(A," if let Some(val)=sharing_update.as_ref().copied(){\n"),(B,"\n }\n")],
 'm_match_ref':[(A," match &sharing_update{Some(val)=>{\n"),(V,"signer_seeds),*val)?;")],
 'm_match_wild':[(B,"\n }_=>{}}\n")],
 'm_match_unit':[(B,"\n }None=>()}\n")],
 'm_iflet_q':[(A," if let Some(val)=sharing_update{\n"),(B,"\n }\n"),(V,"signer_seeds),val).map_err(|e|e)?;")],
}
for k,v in X.items(): open(f'{D}/{k}.py','w').write('EDITS='+repr(v)+'\n')
print(' '.join(X))
