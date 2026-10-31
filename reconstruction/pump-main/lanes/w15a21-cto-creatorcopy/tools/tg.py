# w15a09 tuplelocals genes: (old,new) exact single-occurrence replacements in admin_cto.rs on main 90300f9 (line count kept)
G={}
G['none']=[]
_CB="let cashback=!holder&&st.cashback;"
_HA="if holder{sharing_update=Some(None);(false,false)}"
_NA="else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}"
_NS="else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};"
_TREE="let (collect_old,skip)=if shared{"+_HA+_NA+_NS
_CO="!st.holder_reward&&st.creator!=Pubkey::default()"
_VAL="let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"
_SU="let mut sharing_update:Option<Option<Pubkey>>=None;"
_RET="(holder,cashback,target,sharing_update,collect_old,skip)};"
_HOP="let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;let mut target=target;"
_PA="let pargs=(target,a.bonding_curve.is_holder_reward,fee);"
_PU=" if pool_updated{\n"

# ---- cashback field, per arm ----
# c1: mut local default false; non-holder shared arm and non-shared arm assign
G['c1']=[(_CB,"let mut cashback=false;"),
         (_NA,"else{sharing_update=Some(args.0);cashback=st.cashback;target=a.bonding_curve.creator;(false,true)}}"),
         (_NS,"else{cashback=!holder&&st.cashback;("+_CO+",true)};")]
# c2: deferred init per arm
G['c2']=[(_CB,"let cashback;"),
         (_HA,"if holder{sharing_update=Some(None);cashback=false;(false,false)}"),
         (_NA,"else{sharing_update=Some(args.0);cashback=st.cashback;target=a.bonding_curve.creator;(false,true)}}"),
         (_NS,"else{cashback=!holder&&st.cashback;("+_CO+",true)};")]
# c3: cashback inside the tree tuple (field computed inside the arm)
G['c3']=[(_CB,""),
         (_TREE,"let (collect_old,skip,cashback)=if shared{if holder{sharing_update=Some(None);(false,false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true,st.cashback)}}else{("+_CO+",true,!holder&&st.cashback)};")]
# c4: c1 but the assignment placed last in each arm
G['c4']=[(_CB,"let mut cashback=false;"),
         (_NA,"else{sharing_update=Some(args.0);target=a.bonding_curve.creator;cashback=st.cashback;(false,true)}}"),
         (_NS,"else{cashback=!holder&&st.cashback;("+_CO+",true)};")]
# c5: mut local = st.cashback, holder arm clears, non-shared arm masks
G['c5']=[(_CB,"let mut cashback=st.cashback;"),
         (_HA,"if holder{sharing_update=Some(None);cashback=false;(false,false)}"),
         (_NS,"else{cashback=!holder&&cashback;("+_CO+",true)};")]
# c6: c2 with non-shared arm as if-expr
G['c6']=[(_CB,"let cashback;"),
         (_HA,"if holder{sharing_update=Some(None);cashback=false;(false,false)}"),
         (_NA,"else{sharing_update=Some(args.0);cashback=st.cashback;target=a.bonding_curve.creator;(false,true)}}"),
         (_NS,"else{cashback=if holder{false}else{st.cashback};("+_CO+",true)};")]
# ---- target field ----
# t1: target deferred per arm from validate's value
G['t1']=[(_VAL,"let vt=validate(&st,hopt,fee,new,&holder_key,&sk)?;let target;"),
         (_HA,"if holder{sharing_update=Some(None);target=vt;(false,false)}"),
         (_NS,"else{target=vt;("+_CO+",true)};")]
# t2: target inside the tree tuple
G['t2']=[(_VAL,"let target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"),
         (_TREE,"let (collect_old,skip,target)=if shared{if holder{sharing_update=Some(None);(false,false,target)}else{sharing_update=Some(args.0);(false,true,a.bonding_curve.creator)}}else{("+_CO+",true,target)};")]
# t3: t1 with mut target default from validate kept but holder arm re-assigns (no-op) -> deferred split
G['t3']=[(_VAL,"let vt=validate(&st,hopt,fee,new,&holder_key,&sk)?;let mut target=vt;"),
         (_HA,"if holder{sharing_update=Some(None);target=vt;(false,false)}")]
# ---- sharing_update field ----
# s1: deferred init per arm (no default)
G['s1']=[(_SU,"let sharing_update:Option<Option<Pubkey>>;"),
         (_NS,"else{sharing_update=None;("+_CO+",true)};")]
# s2: su inside tree tuple, holder arm Some(None) (= pre-pl2 form but with tuple order (co,su,skip) vs main)
G['s2']=[(_SU,""),(_TREE,"let (collect_old,skip,sharing_update)=if shared{if holder{(false,false,Some(None))}else{target=a.bonding_curve.creator;(false,true,Some(args.0))}}else{("+_CO+",true,None)};")]
# ---- collect_old / skip fields one at a time ----
# k1: skip as mut local only (collect_old stays tuple) -> tree returns collect_old alone
G['k1']=[(_TREE,"let mut skip=true;let collect_old=if shared{if holder{sharing_update=Some(None);skip=false;false}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;false}}else{"+_CO+"};")]
# k2: collect_old as mut local only, skip from the tree
G['k2']=[(_TREE,"let mut collect_old=false;let skip=if shared{if holder{sharing_update=Some(None);false}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;true}}else{collect_old="+_CO+";true};")]
# k3: deferred collect_old per arm
G['k3']=[(_TREE,"let collect_old;let skip=if shared{if holder{sharing_update=Some(None);collect_old=false;false}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;collect_old=false;true}}else{collect_old="+_CO+";true};")]
# k4: deferred skip per arm
G['k4']=[(_TREE,"let skip;let collect_old=if shared{if holder{sharing_update=Some(None);skip=false;false}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;skip=true;false}}else{skip=true;"+_CO+"};")]
# ---- outer hop per-field ----
G['h1']=[(_HOP,"let (mut target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;")]
# ---- pargs ----
# p1: pargs bound inside the pool arm
G['p1']=[(_PA,""),(_PU," if pool_updated{"+_PA+"\n")]
# p2: pargs deferred, assigned in the pool arm
G['p2']=[(_PA,"let pargs:(Pubkey,bool,Option<u64>);"),(_PU," if pool_updated{pargs=(target,a.bonding_curve.is_holder_reward,fee);\n")]
# p3: pargs fields as separate locals
G['p3']=[(_PA,"let (pt,ph,pf)=(target,a.bonding_curve.is_holder_reward,fee);let pargs=(pt,ph,pf);")]
# p4: pargs with mut fields assigned
G['p4']=[(_PA,"let mut pargs=(target,false,fee);pargs.1=a.bonding_curve.is_holder_reward;")]
# ---- round 2: field computed before vs inside the arm; arm forms; hop field subsets ----
_HOPA="let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;"
G['f1']=[(_CB,_CB+"let co="+_CO+";"),(_NS,"else{(co,true)};")]
G['f2']=[(_SU,_SU+"let co="+_CO+";"),(_NS,"else{(co,true)};")]
G['f3']=[(_TREE,"let collect_old=if shared{if holder{sharing_update=Some(None);false}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;false}}else{"+_CO+"};let skip=!(shared&&holder);")]
G['f4']=[(_CB,_CB+"let skip=!(shared&&holder);"),(_TREE,"let collect_old=if shared{if holder{sharing_update=Some(None);false}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;false}}else{"+_CO+"};")]
G['f5']=[(_VAL,"let su_ns=Some(args.0);"+_VAL),(_NA,"else{sharing_update=su_ns;target=a.bonding_curve.creator;(false,true)}}")]
G['f6']=[(_VAL,"let creator=a.bonding_curve.creator;"+_VAL),(_NA,"else{sharing_update=Some(args.0);target=creator;(false,true)}}")]
G['f7']=[(_SU,_SU+"let creator=a.bonding_curve.creator;"),(_NA,"else{sharing_update=Some(args.0);target=creator;(false,true)}}")]
G['m1']=[(_TREE,"let (collect_old,skip)=match (shared,holder){(true,true)=>{sharing_update=Some(None);(false,false)}(true,false)=>{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}_=>("+_CO+",true)};")]
G['m2']=[(_TREE,"let (collect_old,skip)=match shared{true=>if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)},false=>("+_CO+",true)};")]
G['m3']=[(_TREE,"let (collect_old,skip)=if shared&&holder{sharing_update=Some(None);(false,false)}else if shared{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}else{("+_CO+",true)};")]
G['m4']=[(_TREE,"let (collect_old,skip)=if !shared{("+_CO+",true)}else if !holder{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}else{sharing_update=Some(None);(false,false)};")]
G['o1']=[(_HOPA,"let (target,sharing_update)=Ok::<_,anchor_lang::error::Error>((target,sharing_update))?;")]
G['o2']=[(_HOPA,"let (sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((sharing_update,cashback))?;")]
G['o3']=[(_HOPA,"let (target,sharing_update,cashback,skip)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback,skip))?;")]
G['o4']=[(_HOPA,"let (target,sharing_update,cashback,collect_old)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback,collect_old))?;")]
G['o5']=[(_HOPA,"let (sharing_update,target,cashback)=Ok::<_,anchor_lang::error::Error>((sharing_update,target,cashback))?;")]
G['o6']=[(_HOPA,"let (cashback,target,sharing_update)=Ok::<_,anchor_lang::error::Error>((cashback,target,sharing_update))?;")]
G['o7']=[(_HOPA,"let (target,cashback,sharing_update)=Ok::<_,anchor_lang::error::Error>((target,cashback,sharing_update))?;")]
G['o8']=[(_HOPA,"let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback)).map(|(t,s,c)|(t,s,c))?;")]
# ---- round 3: the inner 6-tuple block: field set and order ----
_PAT="let (_holder,cashback,target,sharing_update,collect_old,skip)={ let st="
def _perm(fields):
    pat="let ("+",".join(fields)+")={ let st="
    ret="("+",".join('holder' if f=='_holder' else f for f in fields)+")};"
    return [(_PAT,pat),(_RET,ret)]
G['q1']=_perm(['cashback','target','sharing_update','collect_old','skip'])
G['q2']=_perm(['target','sharing_update','cashback','_holder','collect_old','skip'])
G['q3']=_perm(['collect_old','skip','_holder','cashback','target','sharing_update'])
G['q4']=_perm(['_holder','target','sharing_update','cashback','collect_old','skip'])
G['q5']=_perm(['_holder','cashback','target','sharing_update','skip','collect_old'])
G['q6']=_perm(['_holder','cashback','sharing_update','target','collect_old','skip'])
G['q7']=_perm(['_holder','collect_old','skip','cashback','target','sharing_update'])
G['q8']=_perm(['skip','collect_old','sharing_update','target','cashback','_holder'])
# ---- round 4: all-per-arm combinations ----
_ALLHEAD="let vt=validate(&st,hopt,fee,new,&holder_key,&sk)?;"
def _all(su_decl,ha,na,ns,head_tail='',tree_pre="let (collect_old,skip)="):
    return [(_CB,""),(_VAL+_SU+_TREE,_ALLHEAD+"let target;let cashback;"+su_decl+head_tail+tree_pre+"if shared{if holder{"+ha+"}else{"+na+"}}else{"+ns+"};")]
G['A1']=_all(_SU,"sharing_update=Some(None);target=vt;cashback=false;(false,false)","sharing_update=Some(args.0);target=a.bonding_curve.creator;cashback=st.cashback;(false,true)","target=vt;cashback=!holder&&st.cashback;("+_CO+",true)")
G['A2']=_all("let sharing_update:Option<Option<Pubkey>>;","sharing_update=Some(None);target=vt;cashback=false;(false,false)","sharing_update=Some(args.0);target=a.bonding_curve.creator;cashback=st.cashback;(false,true)","sharing_update=None;target=vt;cashback=!holder&&st.cashback;("+_CO+",true)")
G['A3']=_all("let sharing_update:Option<Option<Pubkey>>;","sharing_update=Some(None);target=vt;cashback=false;collect_old=false;skip=false;","sharing_update=Some(args.0);target=a.bonding_curve.creator;cashback=st.cashback;collect_old=false;skip=true;","sharing_update=None;target=vt;cashback=!holder&&st.cashback;collect_old="+_CO+";skip=true;",head_tail="let collect_old;let skip;",tree_pre="")
G['A4']=_all(_SU,"sharing_update=Some(None);target=vt;cashback=false;(false,false)","sharing_update=Some(args.0);target=a.bonding_curve.creator;cashback=st.cashback;(false,true)","target=vt;cashback=if holder{false}else{st.cashback};("+_CO+",true)")
# A5: target stays mut (main form), cashback+su per arm (c2+main)
G['A5']=[(_CB,"let cashback;"),(_HA,"if holder{sharing_update=Some(None);cashback=false;(false,false)}"),(_NA,"else{sharing_update=Some(args.0);target=a.bonding_curve.creator;cashback=st.cashback;(false,true)}}"),(_NS,"else{cashback=!holder&&st.cashback;("+_CO+",true)};")]
# A6: A1 with cashback per arm in validate order: non-shared arm first (m4 tree form)
G['A6']=[(_CB,""),(_VAL+_SU+_TREE,_ALLHEAD+"let target;let cashback;"+_SU+"let (collect_old,skip)=if !shared{target=vt;cashback=!holder&&st.cashback;("+_CO+",true)}else if !holder{sharing_update=Some(args.0);target=a.bonding_curve.creator;cashback=st.cashback;(false,true)}else{sharing_update=Some(None);target=vt;cashback=false;(false,false)};")]
# A7: cashback as part of target's per-arm (t1 + c2)
G['A7']=[(_CB,"let cashback;"),(_VAL,"let vt=validate(&st,hopt,fee,new,&holder_key,&sk)?;let target;"),(_HA,"if holder{sharing_update=Some(None);target=vt;cashback=false;(false,false)}"),(_NA,"else{sharing_update=Some(args.0);cashback=st.cashback;target=a.bonding_curve.creator;(false,true)}}"),(_NS,"else{target=vt;cashback=!holder&&st.cashback;("+_CO+",true)};")]
# ---- round 5: f6 family (curve creator bound early, used by the shared non-holder arm) ----
_NAC="else{sharing_update=Some(args.0);target=creator;(false,true)}}"
_HOPT="let hopt=holder;"
_STH="{ let st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator:a.bonding_curve.creator,"
G['g1']=[(_VAL,"let creator=st.creator;"+_VAL),(_NA,_NAC)]
G['g2']=[(_HOPT,"let creator=a.bonding_curve.creator;"+_HOPT),(_NA,_NAC)]
G['g3']=[(_STH,"{ let creator=a.bonding_curve.creator;let st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator:a.bonding_curve.creator,"),(_NA,_NAC)]
G['g4']=[(_VAL,"let creator=&a.bonding_curve.creator;"+_VAL),(_NA,"else{sharing_update=Some(args.0);target=*creator;(false,true)}}")]
G['g5']=[(_STH,"{ let creator=a.bonding_curve.creator;let st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator,"),(_NA,_NAC)]
G['g6']=[("let sk=a.sharing_config.key();let mut target=validate","let sk=a.sharing_config.key();let creator=a.bonding_curve.creator;let mut target=validate"),(_NA,_NAC)]
G['g7']=[(_CB,"let creator=a.bonding_curve.creator;"+_CB),(_NA,_NAC)]
G['g8']=[(_VAL,"let creator=st.creator;"+_VAL),(_NA,_NAC.replace("target=creator","target=creator"))]
G['g9']=[("let args=&(new,);","let args=&(new,a.bonding_curve.creator);"),(_NA,"else{sharing_update=Some(args.0);target=args.1;(false,true)}}")]
G['g10']=[(_VAL,"let creator=a.bonding_curve.creator;"+_VAL),(_NA,"else{sharing_update=Some(args.0);target=creator;(false,true)}}"),(_NS,"else{let _=creator;("+_CO+",true)};")]
# ---- size knobs from $SWARM/w11/sizeknobs-cto.json (w12a13 catalog) ----
import json as _j
for _x in _j.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))['knobs']:
    _e=_x['edit']; _e=_e if isinstance(_e,list) else [_e]
    try: G['K_'+_x['name']]=[(p['old'],p['new']) for p in _e]
    except Exception: pass
# ---- round 6: per-arm cashback (c1) + early creator (g1/g3) ----
_NAc1g="else{sharing_update=Some(args.0);cashback=st.cashback;target=creator;(false,true)}}"
_NSc1="else{cashback=!holder&&st.cashback;("+_CO+",true)};"
G['c1g1']=[(_CB,"let mut cashback=false;"),(_VAL,"let creator=st.creator;"+_VAL),(_NA,_NAc1g),(_NS,_NSc1)]
G['c1g3']=[(_CB,"let mut cashback=false;"),(_STH,"{ let creator=a.bonding_curve.creator;let st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator:a.bonding_curve.creator,"),(_NA,_NAc1g),(_NS,_NSc1)]
G['c1f6']=[(_CB,"let mut cashback=false;"),(_VAL,"let creator=a.bonding_curve.creator;"+_VAL),(_NA,_NAc1g),(_NS,_NSc1)]
G['c1f7']=[(_CB,"let mut cashback=false;"),(_SU,_SU+"let creator=a.bonding_curve.creator;"),(_NA,_NAc1g),(_NS,_NSc1)]
# ---- round 7: st.creator binding positions ----
G['g0']=[(_NA,"else{sharing_update=Some(args.0);target=st.creator;(false,true)}}")]
G['g1a']=[("let args=&(new,);","let creator=st.creator;let args=&(new,);"),(_NA,_NAC)]
G['g1b']=[(_CB,"let creator=st.creator;"+_CB),(_NA,_NAC)]
G['g1c']=[(_HOPT,_HOPT+"let creator=st.creator;"),(_NA,_NAC)]
G['g1d']=[("let sk=a.sharing_config.key();let mut target=validate","let sk=a.sharing_config.key();let creator=st.creator;let mut target=validate"),(_NA,_NAC)]
G['g1e']=[(_SU,_SU+"let creator=st.creator;"),(_NA,_NAC)]
# ==== w15a21 creatorcopy: spellings between g0 (target=st.creator in arm) and g1 (let creator=st.creator before validate) ====
def _na(t): return (_NA,"else{sharing_update=Some(args.0);target="+t+";(false,true)}}")
def _pre(b): return (_VAL,b+_VAL)
G['cc1']=[_pre("let creator:Pubkey=st.creator.clone();"),_na("creator")]
G['cc2']=[_pre("let creator=Pubkey::new_from_array(st.creator.to_bytes());"),_na("creator")]
G['cc3']=[_pre("let creator=st.creator.to_bytes();"),_na("Pubkey::new_from_array(creator)")]
G['cc4']=[_pre("let creator=st.creator.to_bytes();"),_na("Pubkey::from(creator)")]
G['cc5']=[_pre("let CtoState{creator,..}=st;"),_na("creator")]
G['cc6']=[_pre("let &CtoState{creator,..}=&st;"),_na("creator")]
G['cc7']=[_pre("let creator=st.creator;"),_na("creator"),(_CO,"!st.holder_reward&&creator!=Pubkey::default()")]
G['cc8']=[_pre("let creator=&st.creator;"),_na("*creator")]
G['cc9']=[_na("st.creator.clone()")]
G['cc10']=[_na("Pubkey::new_from_array(st.creator.to_bytes())")]
G['cc11']=[("let args=&(new,);","let args=&(new,st.creator);"),_na("args.1")]
G['cc12']=[_pre("let creator=Some(st.creator);"),_na("creator.unwrap()")]
G['cc13']=[_pre("let s=&st;"),_na("s.creator")]
G['cc14']=[("if shared{if holder{","if shared{let creator=st.creator;if holder{"),_na("creator")]
G['cc15']=[_pre("let creator=st.creator;"),_na("creator"),(_NS,"else{(!st.holder_reward&&creator!=Pubkey::default(),true)};")]
G['cc16']=[_pre("let creator=*&st.creator;"),_na("creator")]
G['cc17']=[_pre("let creator=st.creator.to_bytes();"),_na("creator.into()")]
G['cc18']=[_pre("let creator=st.creator;"),_na("creator.clone()")]
G['cc19']=[_na("{let c=&st.creator;*c}")]
G['cc20']=[_pre("let creator=st.creator;"),_na("creator"),("let st=CtoState{","let mut st=CtoState{")]
# ---- round 2 (w15a21): structural creator forms ----
_STRUCT="struct CtoState{creator:Pubkey,"
_STH2="{ let st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator:a.bonding_curve.creator,"
_VALSIG="fn validate(st:&CtoState,"
G['cs1']=[(_STRUCT,"struct CtoState<'c>{creator:&'c Pubkey,"),(_STH2,"{ let st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator:&a.bonding_curve.creator,"),
          (_CO,"!st.holder_reward&&*st.creator!=Pubkey::default()"),_na("*st.creator")]
G['cs1b']=G['cs1'][:3]
_NA0="else{sharing_update=Some(args.0);(false,true)}}"
_HOPB="let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;let mut target=target;"
G['cs2']=[(_NA,_NA0),(_HOPB,"let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;let mut target=if shared&&!_holder{a.bonding_curve.creator}else{target};")]
G['cs3']=[(_NA,_NA0),(_PAT,"let (_holder,cashback,target,sharing_update,collect_old,skip,creator)={ let st="),(_RET,"(holder,cashback,target,sharing_update,collect_old,skip,st.creator)};"),
          (_HOPB,"let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;let mut target=if shared&&!_holder{creator}else{target};")]
G['cs4']=[(_NA,"else{target=st.creator;sharing_update=Some(args.0);(false,true)}}")]
G['cs5']=[(_NA,"else{target=a.bonding_curve.creator;sharing_update=Some(args.0);(false,true)}}")]
G['cs7']=[_pre("let creator=st.creator;"),(_NA,"else{target=creator;sharing_update=Some(args.0);(false,true)}}")]
# cs8: holder arm also writes target explicitly from validate's value via the tuple (target first-class per arm, creator read from st)
G['cs8']=[(_HA,"if holder{sharing_update=Some(None);target=*holder_key;(false,false)}"),_na("st.creator")]
# cs9: shared arm split: creator binding at the head of the shared arm + order target first
G['cs9']=[("if shared{if holder{","if shared{let creator=st.creator;if holder{"),(_NA,"else{target=creator;sharing_update=Some(args.0);(false,true)}}")]
# ---- round 3 (w15a21): arm order x source x payload grid; early-binding positions with target-first arm ----
def _arm(src,first,pay="args.0"):
    su="sharing_update=Some("+pay+");"; tg_="target="+src+";"
    return (_NA,"else{"+(tg_+su if first=='t' else su+tg_)+"(false,true)}}")
for sn,src,pre in (('m','a.bonding_curve.creator',None),('s','st.creator',None),('e','creator',"let creator=st.creator;")):
    for o in ('t','u'):
        for pn,pay in (('a','args.0'),('n','new')):
            G[f'gr_{sn}{o}{pn}']=([_pre(pre)] if pre else [])+[_arm(src,o,pay)]
_POS={'g1a':("let args=&(new,);","let creator=st.creator;let args=&(new,);"),'g1b':(_CB,"let creator=st.creator;"+_CB),'g1c':(_HOPT,_HOPT+"let creator=st.creator;"),
      'g1e':(_SU,_SU+"let creator=st.creator;"),'f6':(_VAL,"let creator=a.bonding_curve.creator;"+_VAL),'f7':(_SU,_SU+"let creator=a.bonding_curve.creator;"),
      'g3':(_STH2,"{ let creator=a.bonding_curve.creator;"+_STH2[2:])}
for k,v in _POS.items(): G[f'tf_{k}']=[v,_arm('creator','t')]
# ---- round 4 (w15a21): st by value / copied, explicit holder-arm target ----
G['cs8']=[(_HA,"if holder{sharing_update=Some(None);target=holder_key;(false,false)}"),_na("st.creator")]
G['cs8m']=[(_HA,"if holder{sharing_update=Some(None);target=holder_key;(false,false)}")]
_VCALL="validate(&st,hopt,fee,new,&holder_key,&sk)?;"
G['sv1']=[(_STRUCT,"#[derive(Clone,Copy)]struct CtoState{creator:Pubkey,"),(_VALSIG,"fn validate(st:CtoState,"),(_VCALL,"validate(st,hopt,fee,new,&holder_key,&sk)?;")]
G['sv2']=[(_STRUCT,"#[derive(Clone,Copy)]struct CtoState{creator:Pubkey,"),(_VCALL,"validate(&{st},hopt,fee,new,&holder_key,&sk)?;")]
G['sv3']=G['sv1']+[_na("st.creator")]
G['sv4']=G['sv2']+[_na("st.creator")]
G['sv5']=[(_STRUCT,"#[derive(Clone,Copy)]struct CtoState{creator:Pubkey,"),(_VCALL,"validate(&st.clone(),hopt,fee,new,&holder_key,&sk)?;"),_na("st.creator")]
# ---- round 5 (w15a21): early creator positions with target-first arm (for the outline base O) ----
G['tf_g5']=[(_STH2,"{ let creator=a.bonding_curve.creator;let st=CtoState{fee_configurable:a.global.creator_fee_configurable,creator,"),_arm('creator','t')]
G['tf_q']=[("let quote_locked={","let creator=a.bonding_curve.creator;let quote_locked={"),_arm('creator','t')]
G['tf_h']=[("let holder_key;let hk=","let creator=a.bonding_curve.creator;let holder_key;let hk="),_arm('creator','t')]
G['tf_a']=[("let a=&ctx.accounts;let mint","let a=&ctx.accounts;let creator=a.bonding_curve.creator;let mint"),_arm('creator','t')]
G['tf_t']=[("let (_holder,cashback,target,sharing_update,collect_old,skip)={ let st=","let creator=a.bonding_curve.creator;let (_holder,cashback,target,sharing_update,collect_old,skip)={ let st="),_arm('creator','t')]
