import json,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a51-cto-sweepjoin/s/')
A=['  if native{let min=','  let r:Result<u64>=if native{let min=']
S={'f1':[A,['   Ok(amount)}\n','   Ok(amount)};let v=r?;Ok(v)\n']],
   'f1c':[A,['   Ok(amount)}\n','   Ok(amount)};Ok(r?)\n']],
   'f1d':[A,['   Ok(amount)}\n','   Ok(amount)};match r{Ok(v)=>Ok(v),Err(e)=>Err(e)}\n']]}
for k,v in S.items(): open(O+k+'.py','w').write('EDITS='+json.dumps(v)+'\n')
