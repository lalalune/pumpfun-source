import json,os,itertools,runpy
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w15a19-cto-c1b01frame')
g=runpy.run_path(O+'/gen.py',run_name='x') if False else None
_CB="let cashback=!holder&&st.cashback;"
_HA="if holder{sharing_update=Some(None);(false,false)}"
_NA0="else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}"
_NS="else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};"
_CO="!st.holder_reward&&st.creator!=Pubkey::default()"
CASH={'':[],
 'c1':[(_CB,"let mut cashback=false;"),("sharing_update=Some(args.0);target=","sharing_update=Some(args.0);cashback=st.cashback;target="),(_NS,"else{cashback=!holder&&st.cashback;("+_CO+",true)};")],
 'c2':[(_CB,"let cashback;"),(_HA,"if holder{sharing_update=Some(None);cashback=false;(false,false)}"),("sharing_update=Some(args.0);target=","sharing_update=Some(args.0);cashback=st.cashback;target="),(_NS,"else{cashback=!holder&&st.cashback;("+_CO+",true)};")],
 'c5':[(_CB,"let mut cashback=st.cashback;"),(_HA,"if holder{sharing_update=Some(None);cashback=false;(false,false)}"),(_NS,"else{cashback=!holder&&cashback;("+_CO+",true)};")],
 'c6':[(_CB,"let cashback;"),(_HA,"if holder{sharing_update=Some(None);cashback=false;(false,false)}"),("sharing_update=Some(args.0);target=","sharing_update=Some(args.0);cashback=st.cashback;target="),(_NS,"else{cashback=if holder{false}else{st.cashback};("+_CO+",true)};")],
}
SIG='holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>'
CALL='validate(&st,hopt,fee,new,&holder_key,&sk)'
RV='read_volatile(holder_key as *const Pubkey as *const u8)'
b01=[(SIG,'holder_key:Pubkey,sharing:&Pubkey)->Result<Pubkey>'),(CALL,'validate(&st,hopt,fee,new,holder_key,&sk)'),
     ('*holder_key}else{','holder_key}else{'),('t==*holder_key{','t==holder_key{'),
     ('unsafe{core::ptr::'+RV+'};if !st','unsafe{core::ptr::read_volatile(&holder_key as *const Pubkey as *const u8)};if !st'),
     (RV+'};}None','read_volatile(&holder_key as *const Pubkey as *const u8)};}None')]
b02=[(a,b) for a,b in b01 if a!='t==*holder_key{']+[('if t==*sharing||t==*holder_key{','if t==holder_key||t==*sharing{')]
KEY={'':[],'b01':b01,'b02':b02}
NAC=("target=a.bonding_curve.creator;","target=creator;")
CRE={'':[],
 'g1':[("let mut target=validate(","let creator=st.creator;let mut target=validate("),NAC],
 'g3':[("{ let st=CtoState{","{ let creator=a.bonding_curve.creator;let st=CtoState{"),NAC],
 'g0':[("target=a.bonding_curve.creator;","target=st.creator;")],
}
def build(names):
    V={}
    for c,k,r in itertools.product(*names):
        n=(c+k+r) or 'm0'
        V[n]=CASH[c]+KEY[k]+CRE[r]
    return V
if __name__=='__main__':
    import sys
    sel=json.loads(sys.argv[1])
    V=build(sel)
    for k,v in V.items(): open(f'{O}/e/{k}.py','w').write('EDITS='+json.dumps(v)+'\n')
    print('\n'.join(V))
