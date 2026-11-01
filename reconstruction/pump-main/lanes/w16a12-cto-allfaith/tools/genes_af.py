# w16a12 allfaith genes: faithful head forms H x faithful tail union T (experiment only).
# Each gene is a list of exact single-occurrence (old,new) replacements or callables s->s; newline count must hold.
# Inherits the swarm library through genes_fu (w16a09) -> genes_lac (w16a04) -> genes_lbw (w15a32) -> ...
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_fu as _S
G=_S.G
def apply(s,names): return _S.apply(s,names)

# ---------------- head forms (main 1f4e396 text) ----------------
_CUR_HR='curve.is_holder_reward=holder.unwrap_or(false);'
_CBX='let cashback=!holder&&st.cashback;'
_CO='!st.holder_reward&&st.creator!=Pubkey::default()'
_ARM=('let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);'
      'target=a.bonding_curve.creator;(false,true)}}else{('+_CO+',true)};(holder,cashback,target,sharing_update,collect_old,skip)};')
# H1 = t_v_h1 (w14a111/w14a142): the curve store reads the block's holder bool instead of re-deriving holder.unwrap_or(false)
G['h1']=[(_CUR_HR,'curve.is_holder_reward=_holder;')]
# H1b: per-arm holder flag (phi of constants in the shared arms, holder in the non-shared arm) feeding the curve store
G['h1b']=[(_CUR_HR,'curve.is_holder_reward=_holder;'),
          (_ARM,'let (hf,collect_old,skip)=if shared{if holder{sharing_update=Some(None);(true,false,false)}else{sharing_update=Some(args.0);'
                'target=a.bonding_curve.creator;(false,false,true)}}else{(holder,'+_CO+',true)};(hf,cashback,target,sharing_update,collect_old,skip)};')]
# H2: H1b + per-arm cashback (w15a32 pa1 form, on main's `if holder` arms)
G['h2']=[(_CUR_HR,'curve.is_holder_reward=_holder;'),(_CBX,''),
         (_ARM,'let (hf,cashback,collect_old,skip)=if shared{if holder{sharing_update=Some(None);(true,false,false,false)}else{sharing_update=Some(args.0);'
               'target=a.bonding_curve.creator;(false,st.cashback,false,true)}}else{(holder,!holder&&st.cashback,'+_CO+',true)};(hf,cashback,target,sharing_update,collect_old,skip)};')]
# H2f: four arms after validate (orig 0xdb8/0x1138/0x1850/0x18b8 write holder/cashback flag spills): non-shared arm split on holder
G['h2f']=[(_CUR_HR,'curve.is_holder_reward=_holder;'),(_CBX,''),
          (_ARM,'let (hf,cashback,collect_old,skip)=if shared{if holder{sharing_update=Some(None);(true,false,false,false)}else{sharing_update=Some(args.0);'
                'target=a.bonding_curve.creator;(false,st.cashback,false,true)}}else if holder{(true,false,'+_CO+',true)}else{(false,st.cashback,'+_CO+',true)};(hf,cashback,target,sharing_update,collect_old,skip)};')]
# H2p: per-arm cashback only (no holder flag change): pa1 on main's arms
G['h2p']=[(_CBX,''),
          (_ARM,'let (collect_old,skip,cashback)=if shared{if holder{sharing_update=Some(None);(false,false,false)}else{sharing_update=Some(args.0);'
                'target=a.bonding_curve.creator;(false,true,st.cashback)}}else{('+_CO+',true,!holder&&st.cashback)};(holder,cashback,target,sharing_update,collect_old,skip)};')]
# FT: fee-tag phi source form (w15a29 phiprobe): validate re-makes the fee (Some(f) after the checks, None otherwise) and returns it;
#     execute uses the validated fee for the curve store and the admin_cto_pool tag, so the fee arg dies in validate.
_RV='unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};'
def _ft(s):
    for a,b in [('->Result<Pubkey>{let holder=hopt==Some(true);','->Result<(Pubkey,Option<u64>)>{let holder=hopt==Some(true);'),
                (' match fee{Some(f)=>{if st.quote_locked{',' let fee=match fee{Some(f)=>{if st.quote_locked{'),
                (_RV+'}None=>{}}',_RV+'Some(f)}None=>None};'),
                (' Ok(target)}pub fn execute',' Ok((target,fee))}pub fn execute'),
                ('let mut target=validate(','let (mut target,fee)=validate('),
                ('cashback,target,sharing_update,collect_old,skip)};','cashback,target,sharing_update,collect_old,skip,fee)};'),
                ('let (_holder,cashback,target,sharing_update,collect_old,skip)={','let (_holder,cashback,target,sharing_update,collect_old,skip,fee)={')]:
        c=s.count(a); assert c==1,('ft',c,a[:80]); s=s.replace(a,b)
    return s
G['ft']=[_ft]
# ---------------- tail forms ----------------
# rev_ff (w14a50 raw-first): token amount read before the frozen flag in the sweep token arm
G['rev_ff']=[('let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;',
              'let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;')]
# o_rs: the ordinary carrier sharing_config_reset:shared (w15a20)
G['o_rs']=[('sharing_config_reset:sharing_update.is_some(),','sharing_config_reset:shared,')]
# FTC (oracle only, NOT landable: its stores are semantic no-ops): fee re-made through a `&mut Option<u64>` out-param, so
#     validate keeps its Result<Pubkey> return layout (ft's Result<(Pubkey,Option<u64>)> drops main's 7 B target.sroa.0
#     piece and shifts every spill slot by 16 B). Separates the fee-tag phi's code value from ft's frame artifact.
def _ftc(s):
    for a,b in [('fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{','fee:&mut Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'),
                (' match fee{Some(f)=>{if st.quote_locked{',' match *fee{Some(f)=>{if st.quote_locked{'),
                (_RV+'}None=>{}}',_RV+'*fee=Some(f);}None=>{*fee=None;}}'),
                ('let hopt=holder;','let hopt=holder;let mut fee=fee;'),
                ('validate(&st,hopt,fee,','validate(&st,hopt,&mut fee,'),
                ('cashback,target,sharing_update,collect_old,skip)};','cashback,target,sharing_update,collect_old,skip,fee)};'),
                ('let (_holder,cashback,target,sharing_update,collect_old,skip)={','let (_holder,cashback,target,sharing_update,collect_old,skip,fee)={')]:
        c=s.count(a); assert c==1,('ftc',c,a[:80]); s=s.replace(a,b)
    return s
G['ftc']=[_ftc]
# S1 / S2 (w16a08 basinbound, ordinary-source form of w14a142's per-arm holder flag e1): validate returns Result<(Pubkey,bool)>
# with the holder flag from its two target arms; the curve store reads it; S1 also takes the event is_holder_reward from the
# holder argument. Copied verbatim from basinbound's e/S1.py, e/S2.py.
import runpy as _rp
_E=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'e')
for _n,_f in (('S1','bbS1'),('S2','bbS2')):
    if os.path.exists(f'{_E}/{_f}.py'): G[_n]=[tuple(x) for x in _rp.run_path(f'{_E}/{_f}.py')['EDITS']]
# FTM (oracle; closure idiom of ftc): validate takes `fee:&mut Option<u64>` and rewrites it in place with
#     `*fee=fee.map(|f|->Result<u64>{..checks..;Ok(f)}).transpose()?;` (the write keeps the value; still a candidate dummy write).
def _ftm(s):
    for a,b in [('fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{','fee:&mut Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'),
                (' match fee{Some(f)=>{if st.quote_locked{',' *fee=fee.map(|f|->Result<u64>{if st.quote_locked{'),
                (_RV+'}None=>{}}',_RV+'Ok(f)}).transpose()?;'),
                ('let hopt=holder;','let hopt=holder;let mut fee=fee;'),
                ('validate(&st,hopt,fee,','validate(&st,hopt,&mut fee,'),
                ('cashback,target,sharing_update,collect_old,skip)};','cashback,target,sharing_update,collect_old,skip,fee)};'),
                ('let (_holder,cashback,target,sharing_update,collect_old,skip)={','let (_holder,cashback,target,sharing_update,collect_old,skip,fee)={')]:
        c=s.count(a); assert c==1,('ftm',c,a[:80]); s=s.replace(a,b)
    return s
G['ftm']=[_ftm]
