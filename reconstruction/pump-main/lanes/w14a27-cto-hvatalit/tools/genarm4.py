import os,sys
d=sys.argv[1]
exec(open(os.path.join(os.path.dirname(__file__),'genarm.py')).read().split("V={")[0].replace("d=sys.argv[1]",""))
CUR=H+C0+'?;'+TV+'?;return Ok(amount);}\n   Ok(amount)}'
V={
'd1_map':'if frozen{'+R+'}else if amount>0{'+C0+'?;return '+TV+'.map(|()|amount);}\n   Ok(amount)}',
'd2_match':'if frozen{'+R+'}else if amount>0{'+C0+'?;match '+TV+'{Ok(())=>return Ok(amount),Err(e)=>return Err(e)}}\n   Ok(amount)}',
'd3_iflet':'if frozen{'+R+'}else if amount>0{'+C0+'?;if let Err(e)='+TV+'{return Err(e);}return Ok(amount);}\n   Ok(amount)}',
'd4_andthen':'if frozen{'+R+'}else if amount>0{'+C0+'.and_then(|()|'+TV+')?;return Ok(amount);}\n   Ok(amount)}',
'd5_rjoin':'(if frozen{'+R+'Ok(())}else if amount>0{'+C0+'?;'+TV+'}else{Ok(())}).map(|()|amount)\n   }',
'd6_rjoin2':'(if frozen{'+R+'Ok(())}else if amount>0{'+C0+'.and_then(|()|'+TV+')}else{Ok(())}).map(|()|amount)\n   }',
'd7_cif':'if frozen{'+R+'}else if amount>0{if let Err(e)='+C0+'{return Err(e);}'+TV+'?;return Ok(amount);}\n   Ok(amount)}',
'd8_rjoin3':'if frozen{'+R+'Ok(amount)}else if amount>0{'+C0+'?;'+TV+'?;return Ok(amount);}else{Ok(amount)}\n   }',
'd9_retq':'if frozen{'+R+'}else if amount>0{'+C0+'?;return '+TV+'.and(Ok(amount));}\n   Ok(amount)}',
'd10_rjoinq':'(if frozen{'+R+'Ok(())}else if amount>0{'+C0+'?;'+TV+'?;return Ok(amount);}else{Ok(())}).map(|()|amount)\n   }',
}
for n,v in V.items():
    open(f'{d}/{n}.py','w').write('EDITS=[(%r,%r)]\n'%(CUR,v))
print(' '.join(V))
