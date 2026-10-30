exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a05-cto-sibclone/edits/_gen.py').read().split('import os')[0])
PA='{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{key:x.key,owner:x.owner,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}'
AT='{let x:&AccountInfo=a.associated_token_program.as_ref();AccountInfo{key:x.key,owner:x.owner,..x.clone()}}'
assert TCF.count(PA)==2 and TCF.count(AT)==1
first=TCF.index(PA); second=TCF.rindex(PA)
def tcf(p1,at,p2):
    t=TCF[:first]+(p1 or PA)+TCF[first+len(PA):second]+(p2 or PA)+TCF[second+len(PA):]
    if at: t=t.replace(AT,at)
    return t
TAI_PA='a.pump_amm.to_account_info()'; TAI_AT='a.associated_token_program.to_account_info()'
S1=(SH,'  '+CALL+'?;')
V={}
V['s1t_p1']=[S1,(TCF,tcf(TAI_PA,None,None))]
V['s1t_at']=[S1,(TCF,tcf(None,TAI_AT,None))]
V['s1t_p2']=[S1,(TCF,tcf(None,None,TAI_PA))]
V['s1t_all']=[S1,(TCF,tcf(TAI_PA,TAI_AT,TAI_PA))]
V['s1t_p12']=[S1,(TCF,tcf(TAI_PA,None,TAI_PA))]
import os
for k,v in V.items(): open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a05-cto-sibclone/edits/'+k+'.py','w').write('EDITS='+repr(v)+'\n')
print(list(V))
