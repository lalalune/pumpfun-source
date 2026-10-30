_VH='->Result<Pubkey>{let holder=hopt==Some(true);'
_EH='let hopt=holder;let holder=hopt==Some(true);'
_289='&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}'
_QL='a.global.whitelisted_quote_mints.contains(&q)};let (holder,cashback,target,sharing_update,collect_old,skip)={'
_VBU=[('fn validate(st:&CtoState,hopt:Option<bool>,','fn validate(st:&CtoState,hopt:u8,'),(_VH,'->Result<Pubkey>{let holder=hopt&1!=0;'),(_289,'&&hopt&1==0{return Err(error!(PumpError::HolderRewardCreatorImmutable));}')]
G['P3U']=[(_QL,'a.global.whitelisted_quote_mints.contains(&q)};let hb=holder.unwrap_or(false);let (holder,cashback,target,sharing_update,collect_old,skip)={'),(_EH,'let hopt=hb as u8;let holder=hb;')]+_VBU
_T306='let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};'
G['TU8']=[(_T306,'let t=if unsafe{*(&new as *const Option<Pubkey> as *const u8)}&1!=0{unsafe{new.unwrap_unchecked()}}else{return Err(error!(PumpError::CtoNewCreatorRequired));};')]
_EX='->Result<()>{ let a=&ctx.accounts;'
_VB=[('fn validate(st:&CtoState,hopt:Option<bool>,','fn validate(st:&CtoState,hopt:bool,'),(_VH,'->Result<Pubkey>{let holder=hopt;'),(_289,'&&!hopt{return Err(error!(PumpError::HolderRewardCreatorImmutable));}')]
_EH3=(_EH,'let hopt=hb;let holder=hb;')
G['P3N']=[(_QL,'a.global.whitelisted_quote_mints.contains(&q)};let hb=holder.unwrap_or(false);let (holder,cashback,target,sharing_update,collect_old,skip)={'),_EH3]+_VB
G['P1U']=[('let mint=a.mint.key();','let mint=a.mint.key();let hb=holder.unwrap_or(false);'),(_EH,'let hopt=hb as u8;let holder=hb;')]+_VBU
G['P0U']=[(_EX,'->Result<()>{ let hb=holder.unwrap_or(false);let a=&ctx.accounts;'),(_EH,'let hopt=hb as u8;let holder=hb;')]+_VBU
G['P2U']=[('holder_key=hk.0;','holder_key=hk.0;let hb=holder.unwrap_or(false);'),(_EH,'let hopt=hb as u8;let holder=hb;')]+_VBU
G['P4U']=[(_EH,'let hb=hopt.unwrap_or(false);let hopt=hb as u8;let holder=hb;'.replace('let hb=hopt','let hopt0=holder;let hb=hopt0').replace('let hopt0=holder;let hb=hopt0.unwrap_or(false);','let hb=holder.unwrap_or(false);'))]+_VBU
G['P3M']=[(_QL,'a.global.whitelisted_quote_mints.contains(&q)};let hb=matches!(holder,Some(true));let (holder,cashback,target,sharing_update,collect_old,skip)={'),(_EH,'let hopt=hb as u8;let holder=hb;')]+_VBU
G['RARH']=[(';let args=&(new,);let sk=a.sharing_config.key();',';let sk=a.sharing_config.key();'),('let hb=holder.unwrap_or(false);let (holder,cashback,target,','let hb=holder.unwrap_or(false);let args=&(new,);let (holder,cashback,target,')]
import json as _j, os as _o
_rp='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a22-cto-rarregs/revg.json'
if _o.path.exists(_rp):
    for _c,_h in _j.load(open(_rp)).items():
        _ok=[(a,b) for a,b,t in _h if t=='chars']
        if _ok: G['R_'+_c[:7]]=_ok
        if len(_ok)>1:
            for _i,_p in enumerate(_ok): G[f'R_{_c[:7]}_{_i}']=[_p]
_ap='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a22-cto-rarregs/aig.json'
if _o.path.exists(_ap):
    for _k,_v in _j.load(open(_ap)).items(): G[_k]=[tuple(x) for x in _v]
_RAWB='unsafe{*(&holder as *const Option<bool> as *const u8)}'
G['V3R']=[(_QL,'a.global.whitelisted_quote_mints.contains(&q)};let hb=holder.unwrap_or(false);let (holder,cashback,target,sharing_update,collect_old,skip)={'),(_EH,'let hopt='+_RAWB+';let holder=hb;')]+_VBU
G['V3R0']=[(_EH,'let hopt='+_RAWB+';let holder=hopt&1!=0;')]+_VBU
G['V3R1']=[(_QL,'a.global.whitelisted_quote_mints.contains(&q)};let hr='+_RAWB+';let (holder,cashback,target,sharing_update,collect_old,skip)={'),(_EH,'let hopt=hr;let holder=hr&1!=0;')]+_VBU
G['V3E']=[(_EX,'->Result<()>{ let hr='+_RAWB+';let a=&ctx.accounts;'),(_EH,'let hopt=hr;let holder=hr&1!=0;')]+_VBU
G['V3U0']=[(_EH,'let hopt=holder.unwrap_or(false) as u8;let holder=hopt&1!=0;')]+_VBU
G['V3U1']=[(_EH,'let hb=holder.unwrap_or(false);let hopt=hb as u8;let holder=hopt&1!=0;')]+_VBU
_SH2='let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==a.pump_fees.key&&!a.sharing_config.data_is_empty();'
_SH1='let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
_HKX='let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;'
G['PDAF']=[(_SH2+_HKX,_HKX+_SH2)]
G['PDA1']=[(_SH1+_HKX,_HKX+_SH1)]
