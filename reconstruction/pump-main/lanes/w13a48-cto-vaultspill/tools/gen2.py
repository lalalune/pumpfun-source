HK="let holder_key;let hk=Pubkey::find_program_address(&[b\"holder-rewards\",mint.as_ref()],&crate::ID);holder_key=hk.0;"
SH="let shared=if a.bonding_curve.creator==a.sharing_config.key()"
V={}
V['hk1']=[(HK+"let quote_locked","let quote_locked"),(SH,HK+SH)]
# hk1 + vault arg forms (late only) - just to see interaction
import runpy
al=runpy.run_path('arg_late.py')['EDITS']
V['hk1_arglate']=V['hk1']+al
for k,v in V.items(): open(k+'.py','w').write('EDITS='+repr(v)+'\n')
