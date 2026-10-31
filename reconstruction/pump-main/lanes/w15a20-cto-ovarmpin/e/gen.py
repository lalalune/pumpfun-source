import json,runpy
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a20-cto-ovarmpin'
ov1a=runpy.run_path(O+'/e/ov1a.py')['EDITS']
X={}
X['sl']=[('let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}',
          'let (collect_old,skip)=if shared{if holder{(false,false)}else{target=a.bonding_curve.creator;(false,true)}}'),
         ('(holder,cashback,target,sharing_update,collect_old,skip)};let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;',
          '(holder,cashback,target,collect_old,skip)};let (target,cashback)=Ok::<_,anchor_lang::error::Error>((target,cashback))?;'),
         ('let (_holder,cashback,target,sharing_update,collect_old,skip)={','let (_holder,cashback,target,collect_old,skip)={'),
         ('match sharing_update{Some(val)=>{','let sharing_update:Option<Option<Pubkey>>=if shared{Some(if _holder{None}else{new})}else{None};match sharing_update{Some(val)=>{')]
X['rs']=[('sharing_config_reset:sharing_update.is_some()','sharing_config_reset:shared')]
X['il']=[('match sharing_update{Some(val)=>{','if let Some(val)=sharing_update{{'),(' }None=>{}}\n let (old_creator',' }}\n let (old_creator')]
X['sr']=X['sl']+X['rs']
for k,v in X.items():
    open(f'{O}/e/m_{k}.py','w').write('EDITS='+json.dumps(v)+'\n')
    open(f'{O}/e/o_{k}.py','w').write('EDITS='+json.dumps(ov1a+v)+'\n')
print(' '.join('m_'+k+' o_'+k for k in X))
