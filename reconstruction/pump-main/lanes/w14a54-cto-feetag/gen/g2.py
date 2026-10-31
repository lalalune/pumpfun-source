import json,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a54-cto-feetag/e/')
BT='(holder,cashback,target,sharing_update,collect_old,skip)'
def thread(var): return [(BT+'={', BT[:-1]+','+var+')={'),(BT+'};', BT[:-1]+','+var+')};')]
SIG='fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'
CALL='let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;'
END='CreatorFeeBpsOutOfRange));}}None=>{}}'
L757='curve.creator_fee_bps=fee.unwrap_or(curve.creator_fee_bps);'
CPI='let pargs=(target,a.bonding_curve.is_holder_reward,fee);'
V={}
def out(ty,init,setv,decl_where='call'):
    e=[(SIG,SIG.replace('sharing:&Pubkey)','sharing:&Pubkey,fo:&mut '+ty+')')),(END,END.replace('));}}None','));}*fo='+setv+';}None'))]
    if decl_where=='call': e.append((CALL,'let mut fo='+init+';'+CALL.replace('&sk)','&sk,&mut fo)')))
    return e
uod='fee.unwrap_or_default()'
V['ob_757']=out('bool','false','true')+thread('fo')+[(L757,'if fo{curve.creator_fee_bps='+uod+';}')]
V['ob_both']=out('bool','false','true')+thread('fo')+[(L757,'if fo{curve.creator_fee_bps='+uod+';}'),(CPI,CPI.replace(',fee)',',fo.then(||'+uod+'))'))]
V['oo_757']=out('Option<u64>','None','Some(f)')+thread('fo')+[(L757,'curve.creator_fee_bps=fo.unwrap_or(curve.creator_fee_bps);')]
V['oo_cpi']=out('Option<u64>','None','Some(f)')+thread('fo')+[(CPI,CPI.replace(',fee)',',fo)'))]
V['oo_both']=out('Option<u64>','None','Some(f)')+thread('fo')+[(L757,'curve.creator_fee_bps=fo.unwrap_or(curve.creator_fee_bps);'),(CPI,CPI.replace(',fee)',',fo)'))]
V['ou_757']=out('u64','0','1')+thread('fo')+[(L757,'if fo!=0{curve.creator_fee_bps='+uod+';}')]
V['ou8_757']=out('u8','0','1')+thread('fo')+[(L757,'if fo!=0{curve.creator_fee_bps='+uod+';}')]
# value-only Option out param, read only at 757 via match on fo with fee value
V['oo_757m']=out('Option<u64>','None','Some(f)')+thread('fo')+[(L757,'if let Some(f)=fo{curve.creator_fee_bps=f;}')]
for k,v in V.items(): open(O+k+'.py','w').write('EDITS='+json.dumps(v)+'\n')
print(' '.join(V))
