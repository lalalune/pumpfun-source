import json,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a54-cto-feetag/e/')
SIG=('->Result<Pubkey>{let holder=hopt==Some(true);',)
BT='(holder,cashback,target,sharing_update,collect_old,skip)'
def thread(var):  # carry var out of the outer block
    return [(BT+'={', BT[:-1]+','+var+')={'),(BT+'};', BT[:-1]+','+var+')};')]
L757='curve.creator_fee_bps=fee.unwrap_or(curve.creator_fee_bps);'
V={}
# F2: validate returns re-materialised Option<u64>; 757 + CPI read it (ftag2 in source)
opt_val=[('->Result<Pubkey>{let holder=hopt==Some(true);','->Result<(Pubkey,Option<u64>)>{let holder=hopt==Some(true);'),
 (' match fee{Some(f)=>{if st.quote_locked',' let fee=match fee{Some(f)=>{if st.quote_locked'),
 ('CreatorFeeBpsOutOfRange));}}None=>{}}','CreatorFeeBpsOutOfRange));}Some(f)}None=>None};'),
 (' Ok(target)}pub fn',' Ok((target,fee))}pub fn')]
V['opt_both']=opt_val+[('let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;','let (mut target,fee)=validate(&st,hopt,fee,new,&holder_key,&sk)?;')]+thread('fee')
V['opt_757']=opt_val+[('let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;','let (mut target,fee2)=validate(&st,hopt,fee,new,&holder_key,&sk)?;')]+thread('fee2')+[(L757,'if let Some(f)=fee2{curve.creator_fee_bps=f;}')]
V['opt_cpi']=opt_val+[('let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;','let (mut target,fee2)=validate(&st,hopt,fee,new,&holder_key,&sk)?;')]+thread('fee2')+[('let pargs=(target,a.bonding_curve.is_holder_reward,fee);','let pargs=(target,a.bonding_curve.is_holder_reward,fee2);')]
# bool forms
bool_val=[('->Result<Pubkey>{let holder=hopt==Some(true);','->Result<(Pubkey,bool)>{let holder=hopt==Some(true);'),
 (' match fee{Some(f)=>{if st.quote_locked',' let fs=match fee{Some(f)=>{if st.quote_locked'),
 ('CreatorFeeBpsOutOfRange));}}None=>{}}','CreatorFeeBpsOutOfRange));}true}None=>false};'),
 (' Ok(target)}pub fn',' Ok((target,fs))}pub fn'),
 ('let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;','let (mut target,fs)=validate(&st,hopt,fee,new,&holder_key,&sk)?;')]+thread('fs')
V['bool_757uod']=bool_val+[(L757,'if fs{curve.creator_fee_bps=fee.unwrap_or_default();}')]
V['bool_757nest']=bool_val+[(L757,'if fs{if let Some(f)=fee{curve.creator_fee_bps=f;}}')]
V['bool_both']=bool_val+[(L757,'if fs{curve.creator_fee_bps=fee.unwrap_or_default();}'),('let pargs=(target,a.bonding_curve.is_holder_reward,fee);','let pargs=(target,a.bonding_curve.is_holder_reward,if fs{Some(fee.unwrap_or_default())}else{None});')]
V['bool_cpi_then']=bool_val+[('let pargs=(target,a.bonding_curve.is_holder_reward,fee);','let pargs=(target,a.bonding_curve.is_holder_reward,fs.then(||fee.unwrap_or_default()));')]
# is_some captured at exit
V['issome']=[('->Result<Pubkey>{let holder=hopt==Some(true);','->Result<(Pubkey,bool)>{let holder=hopt==Some(true);'),(' Ok(target)}pub fn',' Ok((target,fee.is_some()))}pub fn'),('let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;','let (mut target,fs)=validate(&st,hopt,fee,new,&holder_key,&sk)?;')]+thread('fs')+[(L757,'if fs{curve.creator_fee_bps=fee.unwrap_or_default();}')]
# if-let sets a bool
V['iflet_bool']=[('->Result<Pubkey>{let holder=hopt==Some(true);','->Result<(Pubkey,bool)>{let holder=hopt==Some(true);'),
 (' match fee{Some(f)=>{if st.quote_locked',' let mut fs=false;if let Some(f)=fee{if st.quote_locked'),
 ('CreatorFeeBpsOutOfRange));}}None=>{}}','CreatorFeeBpsOutOfRange));}fs=true;}'),
 (' Ok(target)}pub fn',' Ok((target,fs))}pub fn'),
 ('let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;','let (mut target,fs)=validate(&st,hopt,fee,new,&holder_key,&sk)?;')]+thread('fs')+[(L757,'if fs{curve.creator_fee_bps=fee.unwrap_or_default();}')]
for k,v in V.items(): open(O+k+'.py','w').write('EDITS='+json.dumps(v)+'\n')
print(' '.join(V))
