import json,os
E=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a52-cto-prep410/e')
ARM="else{target=st.creator;(false,Some(args.0),true)}"
ARM2="else{(false,Some(args.0),true)}"
ST="  curve.creator=target;\n"
PA="let pargs=(target,a.bonding_curve.is_holder_reward,fee);"
PA2="let pargs=(a.bonding_curve.creator,a.bonding_curve.is_holder_reward,fee);"
V={}
V['ts_if']=[(ARM,ARM2),(ST,"  if !(shared&&!holder){curve.creator=target;}\n"),(PA,PA2)]
V['ts_if2']=[(ARM,ARM2),(ST,"  if !shared||holder{curve.creator=target;}\n"),(PA,PA2)]
V['ts_sel']=[(ARM,ARM2),(ST,"  curve.creator=if shared&&!holder{old_creator}else{target};\n"),(PA,PA2)]
V['ts_su']=[(ARM,ARM2),(ST,"  if let Some(Some(_))=sharing_update{}else{curve.creator=target;}\n"),(PA,PA2)]
V['ts_pa']=[(PA,PA2)]
V['ts_sel_t']=[(ARM,ARM2),(ST,"  curve.creator=if shared&&!holder{old_creator}else{target};\n")]
for k,v in V.items(): open(f'{E}/{k}.py','w').write('EDITS='+json.dumps(v)+'\n')
print(' '.join(V))
