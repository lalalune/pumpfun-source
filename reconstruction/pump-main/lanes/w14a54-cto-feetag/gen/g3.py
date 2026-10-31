import json,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a54-cto-feetag/e/')
T='let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{target=st.creator;(false,Some(args.0),true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};'
H='let (collect_old,sharing_update,skip)='
A='(false,Some(None),false)'; B='{target=st.creator;(false,Some(args.0),true)}'; C='(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)'
V={
't_hs_and':H+'if holder&&shared{'+A+'}else if shared'+B+'else{'+C+'};',
't_h_nest':H+'if holder{if shared{'+A+'}else{'+C+'}}else if shared'+B+'else{'+C+'};',
't_m_hs':H+'match (holder,shared){(true,true)=>'+A+',(false,true)=>'+B+',_=>'+C+'};',
't_m_sh':H+'match (shared,holder){(true,true)=>'+A+',(true,false)=>'+B+',_=>'+C+'};',
't_nh_and':H+'if !holder&&shared'+B+'else if shared{'+A+'}else{'+C+'};',
't_sh_and':H+'if shared&&holder{'+A+'}else if shared'+B+'else{'+C+'};',
}
for k,v in V.items(): open(O+k+'.py','w').write('EDITS='+json.dumps([(T,v)])+'\n')
print(' '.join(V))
