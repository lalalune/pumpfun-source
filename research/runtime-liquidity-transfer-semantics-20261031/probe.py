import hashlib,json,pathlib,struct,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'tests'))
import test_pump_amm_liquidity_captured as m

def delegate(mint,owner,allowance,delegate=None,amount=10**12,extension=False):
 b=bytearray(m.token_account(mint,owner,amount,extension=extension))
 struct.pack_into('<I',b,72,1)
 b[76:108]=bytes(m.USER.pubkey() if delegate is None else delegate)
 struct.pack_into('<Q',b,121,allowance)
 return bytes(b)

cases=[]
for prog in (m.TOKEN,m.TOKEN22):
 for allowance in (0,399999,400000,400001,10**12):
  cases.append((f'base_delegate_{prog}_{allowance}',{'base_owner':prog,'ub_data':delegate(m.BASE,m.OTHER,allowance)}))
 for allowance in (0,400000,400001):
  cases.append((f'owner_is_delegate_{prog}_{allowance}',{'base_owner':prog,'ub_data':delegate(m.BASE,m.USER.pubkey(),allowance)}))
 cases.append((f'other_delegate_owner_authority_{prog}',{'base_owner':prog,'ub_data':delegate(m.BASE,m.USER.pubkey(),400000,m.OTHER)}))
 cases.append((f'other_delegate_not_owner_{prog}',{'base_owner':prog,'ub_data':delegate(m.BASE,m.CREATOR,400000,m.OTHER)}))
for allowance in (0,202020,202021,10**12):
 cases.append((f'quote_fee_delegate_{allowance}',{'fee':(100,10**9),'uq_data':delegate(m.QUOTE,m.OTHER,allowance,extension=True)}))
for label,c in [('baseline',{}),('insufficient_wrong_mint',{'ub_amt':1,'ub_mint':m.OTHER}),('insufficient_wrong_owner',{'ub_amt':1,'ub_owner':m.OTHER}),('insufficient_delegate',{'ub_data':delegate(m.BASE,m.OTHER,400000,amount=1)})]:cases.append((label,c))
answers=subprocess.run([sys.argv[1]],input=''.join(m.host_line(c)+'\n' for _,c in cases),capture_output=True,text=True,check=True).stdout.splitlines()
if len(answers)!=len(cases):raise ValueError('native host result count differs')
checker=m.PumpAmmLiquidityCapturedTests()
rows=[]
for (name,c),answer in zip(cases,answers):
 r=m.run_captured(c)
 try:checker.assert_matches(answer,r); verdict='match'; mismatch=''
 except AssertionError as e:verdict='mismatch';mismatch=str(e)[:300]
 rows.append({'name':name,'host_outcome':answer.split(',')[0],'captured_error':r['error'],'events':len(r['events']),'verdict':verdict,'mismatch':mismatch})
print(json.dumps({'base':'90300f9d2efe3ef014b116172251a41bfb104d78','images':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (m.AMM_ELF,m.TOKEN_ELF,m.TOKEN22_ELF)},'host':sys.argv[1],'count':len(rows),'mismatches':sum(r['verdict']=='mismatch' for r in rows),'rows':rows},indent=2))
