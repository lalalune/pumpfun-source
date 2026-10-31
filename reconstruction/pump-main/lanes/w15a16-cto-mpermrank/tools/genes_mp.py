# w15a16 mpermrank genes: stitch15 library (w15a03, copied) + this lane's extra archived leads
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_s15 as _S
G=_S.G
def apply(s,names): return _S.apply(s,names)
# ---- fru family (w14a133 fru1 generalised): struct update `..*x` for the trailing Copy fields of CPI AccountInfo literal k ----
import re as _re
_LIT=_re.compile(r'\{let x:&AccountInfo=[^}]*\}\}')
_CP={'owner','key','rent_epoch','is_signer','is_writable','executable'}
def _fru(k,keep_all_before=True):
    def g(s):
        ms=list(_LIT.finditer(s)); m=ms[k-1]; t=m.group(0)
        head,body=t.split('AccountInfo{',1); body=body[:-2]
        fs=[f for f in body.split(',')]
        names=[f.split(':')[0] for f in fs]
        last=max(i for i,n in enumerate(names) if n in ('lamports','data'))
        if keep_all_before: kept=fs[:last+1]
        else: kept=[f for f in fs if f.split(':')[0] in ('lamports','data')]
        assert all(n in _CP for n in names[last+1:]) or not keep_all_before,(k,names)
        t2=head+'AccountInfo{'+','.join(kept)+',..*x}}'
        return s[:m.start()]+t2+s[m.end():]
    return [g]
for _k in range(1,10):
    G[f'fru{_k}']=_fru(_k)
    G[f'frl{_k}']=_fru(_k,False)
# ---- w15a01 devolfill genes (copied): devol (both read_volatile placeholders removed, -8 B) and l2l_* (CtoState field last) ----
_V='unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};'
G['devol']=[("fn validate(st:&CtoState,","fn validate(st:&mut CtoState,"),
 (" if st.holder_reward&&!(hopt==Some(true)){"," let hr=st.holder_reward;if hr&&!(hopt==Some(true)){"),
 (" if holder&&!st.holder_reward&&!st.holder_enabled{"," if holder&&!hr&&!st.holder_enabled{"),
 ("{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}"+_V+"}","{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}st.fee_configurable=false;}"),
 (" let st=CtoState{"," let mut st=CtoState{"),("validate(&st,","validate(&mut st,"),
 (_V+"if !st.fee_configurable{","if !st.fee_configurable{")]
_L1='fee_configurable:a.global.creator_fee_configurable,creator:a.bonding_curve.creator,max_fee:a.global.max_configurable_creator_fee_bps,mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled:a.global.is_holder_reward_enabled'
_G1=_L1.split(',')
for _i,_x in enumerate(_G1):
    if _i==0 or _i==len(_G1)-1: continue
    G['l2l_'+_x.split(':')[0]]=[('CtoState{'+_L1+'}','CtoState{'+','.join(_G1[:_i]+_G1[_i+1:]+[_x])+'}')]
# ---- w15a01 mv_i_j (CtoState literal: move field i to position j, on 86e2a6b's literal) ----
_FN=_L1.split(',')
for _i in range(len(_FN)):
    for _j in range(len(_FN)):
        if _i==_j or _j==_i+1: continue
        _l=_FN[:]; _x=_l.pop(_i); _l.insert(_j if _j<_i else _j-1,_x)
        if _l==_FN: continue
        G[f'mv_{_i}_{_j}']=[('CtoState{'+_L1+'}','CtoState{'+','.join(_l)+'}')]
# ---- w15a17 s_tai2: TCF accounts `program` sub-literal (CPI literal #4) as a.pump_amm.to_account_info() ----
G['s_tai2']=[('{let x:&AccountInfo=a.pump_amm.as_ref();AccountInfo{key:x.key,owner:x.owner,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,executable:x.executable}}','a.pump_amm.to_account_info()')]
# ---- arbitrary CtoState literal order: ord_<digits> over 86e2a6b's literal fields (0 fee_configurable,1 creator,2 max_fee,
#      3 mayhem,4 holder_reward,5 cashback,6 quote_locked,7 holder_enabled) ----
import itertools as _it
def _ord(p): return [('CtoState{'+_L1+'}','CtoState{'+','.join(_FN[int(c)] for c in p)+'}')]
for _p in _it.permutations('01234567'):
    if '5' in _p[:2]: G['ord_'+''.join(_p)]=_ord(''.join(_p))
# ---- w15a01 validate call-site spellings (devol form) + t1n via args.0 ----
_C='validate(&mut st,hopt,fee,new,&holder_key,&sk)?'
G['c_sk']=[(_C,'validate(&mut st,hopt,fee,new,&holder_key,&a.sharing_config.key())?')]
G['c_hk']=[(_C,'validate(&mut st,hopt,fee,new,&hk.0,&sk)?')]
G['c_new']=[(_C,'validate(&mut st,hopt,fee,args.0,&holder_key,&sk)?')]
G['c_hold']=[(_C,'validate(&mut st,holder,fee,new,&holder_key,&sk)?')]
G['t1a']=[("if shared{if new.is_none(){","if shared{if args.0.is_none(){")]
