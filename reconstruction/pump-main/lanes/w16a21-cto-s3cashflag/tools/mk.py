#!/usr/bin/env python3
"""mk.py: write e/<name>.py edit sets = S3n's 7 edits + per-variant cashback-flag edits (applied sequentially, line count kept)."""
import json,runpy,sys
O=__import__("os").environ.get("OUT","/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a21-cto-s3cashflag")
SRC='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a21-cto-s3cashflag/programs/pump/src/creator/admin_cto.rs'
S3N=[tuple(x) for x in runpy.run_path(O+'/e/S3n.py')['EDITS']]
# --- building blocks (strings as they stand after S3n) ---
SIG=("hf:&mut bool)->Result<Pubkey>{","hf:&mut bool,cf:&mut bool)->Result<Pubkey>{")
HARM=("*hf=true;*holder_key}","*hf=true;*cf=false;*holder_key}")
WARM=("*hf=false;t};","*hf=false;*cf=st.cashback;t};")
HEADCB=("let cashback=!holder&&st.cashback;let args","let args")
CALL=("let mut hf=false;let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,&mut hf)?;",
      "let mut hf=false;let mut cf=false;let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,&mut hf,&mut cf)?;")
RET=("(hf,cashback,target,sharing_update,collect_old,skip)}","(hf,cf,target,sharing_update,collect_old,skip)}")
EVCB=("is_cashback_coin:a.bonding_curve.is_cashback_coin,","is_cashback_coin:cashback,")
VLOC=(" let cashback=if holder{false}else{st.cashback};\n"," \n")
FEECF=("  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}","  if *cf{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}")
CORE=[SIG,HARM,WARM,HEADCB,CALL,RET]
V={}
V['c1']=CORE                                  # cf per arm, fee check on validate's local, event re-reads curve
V['c2']=CORE+[EVCB]                           # + event reads cf
V['c3']=CORE+[VLOC,FEECF]                     # fee check reads *cf
V['c4']=CORE+[VLOC,FEECF,EVCB]
# flag written after the fee checks (end of validate), holder arm keeps nothing
V['c5']=[SIG,HEADCB,CALL,RET,(" Ok(target)}pub fn execute"," *cf=cashback;Ok(target)}pub fn execute")]
V['c6']=V['c5']+[EVCB]
# only the wallet arm writes (init false covers the holder arm)
V['c7']=[SIG,WARM,HEADCB,CALL,RET]
V['c8']=V['c7']+[EVCB]
# cashback derived from hf in execute (no cf), after validate
V['c9']=[HEADCB,("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,&mut hf)?;","let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,&mut hf)?;let cashback=!hf&&st.cashback;")]
V['c10']=V['c9']+[EVCB]
# one &mut (bool,bool) carries both flags
TUP=[("hf:&mut bool)->Result<Pubkey>{","fl:&mut (bool,bool))->Result<Pubkey>{"),
     ("*hf=true;*holder_key}","*fl=(true,false);*holder_key}"),
     ("*hf=false;t};","*fl=(false,st.cashback);t};"),HEADCB,
     ("let mut hf=false;let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,&mut hf)?;","let mut fl=(false,false);let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,&mut fl)?;"),
     ("(hf,cashback,target,sharing_update,collect_old,skip)}","(fl.0,fl.1,target,sharing_update,collect_old,skip)}")]
V['t1']=TUP
V['t2']=TUP+[EVCB]
# field-wise tuple writes
TUPF=[TUP[0],("*hf=true;*holder_key}","fl.0=true;fl.1=false;*holder_key}"),("*hf=false;t};","fl.0=false;fl.1=st.cashback;t};")]+TUP[3:]
V['t3']=TUPF
V['t4']=TUPF+[EVCB]
# cf written at the head of each arm
HARMH=(" let target=if holder{if new.is_some()"," let target=if holder{*cf=false;if new.is_some()")
WARMH=("*holder_key}else{\n","*holder_key}else{*cf=st.cashback;\n")
V['c11']=[SIG,HARMH,WARMH,HEADCB,CALL,RET]
V['c12']=V['c11']+[EVCB]
def build(name,extra):
    s=open(SRC).read(); n0=s.count('\n'); E=S3N+list(extra)
    for a,b in E:
        c=s.count(a); assert c==1,(name,c,a[:100]); s=s.replace(a,b)
    assert s.count('\n')==n0,(name,'lines')
    json.dump(E,open(f'{O}/e/{name}.py.json','w'))
    open(f'{O}/e/{name}.py','w').write('EDITS='+json.dumps(E)+'\n')
    return s
# ---- second batch ----
# c13: execute's block derives cashback from the per-arm holder flag as an if/else (i1 select, threadable into validate's arms)
CALLS3=("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,&mut hf)?;",)
V['c13']=[HEADCB,(CALLS3[0],CALLS3[0]+"let cashback=if hf{false}else{st.cashback};")]
V['c13e']=V['c13']+[EVCB]
# c14: S3n + per-arm cashback in execute's shared/holder arms (h2p/pa1 on S3's block)
_CO='!st.holder_reward&&st.creator!=Pubkey::default()'
ARMS3=('let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);'
      'target=a.bonding_curve.creator;(false,true)}}else{('+_CO+',true)};(hf,cashback,target,sharing_update,collect_old,skip)};')
V['c14']=[HEADCB,(ARMS3,'let (collect_old,skip,cashback)=if shared{if holder{sharing_update=Some(None);(false,false,false)}else{sharing_update=Some(args.0);'
                'target=a.bonding_curve.creator;(false,true,st.cashback)}}else{('+_CO+',true,!holder&&st.cashback)};(hf,cashback,target,sharing_update,collect_old,skip)};')]
V['c14e']=V['c14']+[EVCB]
# c15: the holder arm clears st.cashback (validate takes &mut CtoState); fee check and curve store read st.cashback
V['c15']=[("fn validate(st:&CtoState,","fn validate(st:&mut CtoState,"),
          ("*hf=true;*holder_key}","*hf=true;st.cashback=false;*holder_key}"),
          VLOC,("  if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}","  if st.cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}"),
          HEADCB,("let st=CtoState{","let mut st=CtoState{"),
          ("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,&mut hf)?;","let mut target=validate(&mut st,hopt,fee,new,&holder_key,&sk,&mut hf)?;"),
          ("(hf,cashback,target,sharing_update,collect_old,skip)}","(hf,st.cashback,target,sharing_update,collect_old,skip)}")]
V['c15e']=V['c15']+[EVCB]
# c18: cf written right after validate's cashback local (before the fee checks), not in the arms
V['c18']=[SIG,HEADCB,CALL,RET,(" let cashback=if holder{false}else{st.cashback};\n"," let cashback=if holder{false}else{st.cashback};*cf=cashback;\n")]
V['c18e']=V['c18']+[EVCB]


# ---- third batch ----
# c16: validate returns Result<(Pubkey,bool)> carrying the per-arm cashback as an SSA bool (i1 phi), hf stays the out-param
V['c16']=[("hf:&mut bool)->Result<Pubkey>{","hf:&mut bool)->Result<(Pubkey,bool)>{"),
          ("*hf=true;*holder_key}","*hf=true;(*holder_key,false)}"),("*hf=false;t};","*hf=false;(t,st.cashback)};"),HEADCB,
          ("let mut hf=false;let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,&mut hf)?;","let mut hf=false;let (mut target,cf)=validate(&st,hopt,fee,new,&holder_key,&sk,&mut hf)?;"),
          RET]
V['c16e']=V['c16']+[EVCB]
# c19: S3n + four arms in execute's block (non-shared arm split on holder), cashback per arm
V['c19']=[HEADCB,(ARMS3,'let (collect_old,skip,cashback)=if shared{if holder{sharing_update=Some(None);(false,false,false)}else{sharing_update=Some(args.0);'
                'target=a.bonding_curve.creator;(false,true,st.cashback)}}else if holder{('+_CO+',true,false)}else{('+_CO+',true,st.cashback)};(hf,cashback,target,sharing_update,collect_old,skip)};')]
V['c19e']=V['c19']+[EVCB]


# ---- fourth batch ----
# c20: S3n + per-arm cashback in execute's arms, the non-shared arm reuses the head cashback (head computation kept)
V['c20']=[(ARMS3,'let (collect_old,skip,cashback)=if shared{if holder{sharing_update=Some(None);(false,false,false)}else{sharing_update=Some(args.0);'
                'target=a.bonding_curve.creator;(false,true,st.cashback)}}else{('+_CO+',true,cashback)};(hf,cashback,target,sharing_update,collect_old,skip)};')]
V['c20e']=V['c20']+[EVCB]


# ---- fifth batch: repay the freed bytes with faithful pieces (g1 creator copy, Fa validate reads args.0) ----
G1=[("let sk=a.sharing_config.key();let mut hf=false;","let sk=a.sharing_config.key();let creator=st.creator;let mut hf=false;"),
    ("sharing_update=Some(args.0);target=a.bonding_curve.creator;","sharing_update=Some(args.0);target=creator;")]
FA=[("validate(&st,hopt,fee,new,","validate(&st,hopt,fee,args.0,")]
for b in ('c5','c20'):
    V[b+'g']=V[b]+G1; V[b+'F']=V[b]+FA; V[b+'gF']=V[b]+G1+FA

if __name__=='__main__':
    names=sys.argv[1:] or list(V)
    for k in names:
        try: build(k,V[k]); print(k,'ok',len(V[k]))
        except AssertionError as e: print(k,'FAIL',e)
