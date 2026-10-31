import runpy
g=runpy.run_path('common.py'); globals().update({k:v for k,v in g.items() if k.isupper()})
V={}
EK="#[derive(Clone,Copy)]enum Kind{Holder,Wallet{cashback:bool}}"
CBX="let cashback=!holder&&st.cashback;"
K1=[(STRUCT,STRUCT+EK),(T0,T0.replace(CBX,"let cashback=if holder{Kind::Holder}else{Kind::Wallet{cashback:st.cashback}};"))]
V['k1']=K1+[(HR,"  curve.is_holder_reward=matches!(cashback,Kind::Holder);"),(CB,"  curve.is_cashback_coin=matches!(cashback,Kind::Wallet{cashback:true});")]
V['k1b']=K1+[(CB,"  curve.is_cashback_coin=matches!(cashback,Kind::Wallet{cashback:true});")]
V['k1c']=K1+[(CB,"  curve.is_cashback_coin=match cashback{Kind::Wallet{cashback}=>cashback,Kind::Holder=>false};")]
V['k1d']=K1+[(HR,"  curve.is_holder_reward=matches!(cashback,Kind::Holder);"),(CB,"  curve.is_cashback_coin=match cashback{Kind::Wallet{cashback}=>cashback,Kind::Holder=>false};")]
# k2: Kind built after validate (validate-exit position) in the tree
K2=[(STRUCT,STRUCT+EK),(T0,T0.replace(CBX,"").replace("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let cashback=if holder{Kind::Holder}else{Kind::Wallet{cashback:st.cashback}};"))]
V['k2']=K2+[(HR,"  curve.is_holder_reward=matches!(cashback,Kind::Holder);"),(CB,"  curve.is_cashback_coin=matches!(cashback,Kind::Wallet{cashback:true});")]
V['k2b']=K2+[(CB,"  curve.is_cashback_coin=matches!(cashback,Kind::Wallet{cashback:true});")]
# k3: Option<bool> as the sum type (None=holder, Some(cb)=wallet)
K3=[(T0,T0.replace(CBX,"let cashback=if holder{None}else{Some(st.cashback)};"))]
V['k3']=K3+[(CB,"  curve.is_cashback_coin=cashback==Some(true);")]
V['k3b']=K3+[(HR,"  curve.is_holder_reward=cashback.is_none();"),(CB,"  curve.is_cashback_coin=cashback.unwrap_or(false);")]
for k,v in V.items():
    open(k+'.py','w').write('EDITS='+repr(v)+'\n')
print(list(V))
