import json,os,glob
E=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a52-cto-prep410/e')
ld=lambda n: [tuple(x) for x in json.load(open(f'{E}/{n}.py'.replace('.py','.py')).read()[6:]) if False] 
def L(n):
    s=open(f'{E}/{n}.py').read(); assert s.startswith('EDITS='); return json.loads(s[6:])
SH=[[" match sharing_update{Some(val)=>{\n"," if let Some(val)=sharing_update{{\n"],["signer_seeds),val)?;\n\n }None=>{}}\n","signer_seeds),val)?;\n\n }}\n"]]
TP=[["let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;","let pool_updated=a.pool.data_len()!=0 && a.pool.owner==&AMM;"]]
SUF=L('t_ord_suf')[0][1]
# comem applied on top of suf tuple
SUFCM=[[L('t_ord_suf')[0][0], SUF.replace("(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)","(None,st.creator!=Pubkey::default()&&!st.holder_reward,true)")]]
SUFCA=[[L('t_ord_suf')[0][0], SUF.replace("(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)","(None,!st.holder_reward&(st.creator!=Pubkey::default()),true)")]]
V={'sh':SH,'tp':TP,'suf_cm':SUFCM,'suf_ca':SUFCA,'suf_cm_sh':SUFCM+SH,'suf_cm_tp':SUFCM+TP,'suf_ca_sh':SUFCA+SH,'suf_sh_tp':L('t_ord_suf')+SH+TP,'suf_sh':L('t_ord_suf')+SH,'suf_tp':L('t_ord_suf')+TP,'cm_k8':None}
del V['cm_k8']
for k,v in V.items(): open(f'{E}/{k}.py','w').write('EDITS='+json.dumps(v)+'\n')
print(' '.join(V))
