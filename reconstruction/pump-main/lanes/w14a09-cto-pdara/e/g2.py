# partner library on top of pda (main 769f331). trial name = genes joined by '+'; 'pda' implied first unless name starts with 'nopda+'
import json,os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import gen
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P=json.load(open(O+'/e/partners.json'))
_S=gen._S; _H=gen._H
_QL='let quote_locked=crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global);'
_HKF='Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID)'
H={}
H['hL']=[('let shared=a.sharing_config.key()==a.bonding_curve.creator&&','let shared=a.bonding_curve.creator==a.sharing_config.key()&&')]
H['hK1']=[(_H,'let holder_key='+_HKF+'.0;')]
H['hK2']=[(_H,'let (holder_key,_)='+_HKF+';')]
H['hK3']=[(_H,'let hk='+_HKF+';let holder_key=hk.0;')]
H['hSK']=[('let a=&ctx.accounts;let mint=a.mint.key();','let a=&ctx.accounts;let mint=a.mint.key();let sk=a.sharing_config.key();'),('let shared=a.sharing_config.key()==','let shared=sk=='),('let args=&(new,);let sk=a.sharing_config.key();','let args=&(new,);')]
H['hSKp']=[(_H,_H+'let sk=a.sharing_config.key();'),('let shared=a.sharing_config.key()==','let shared=sk=='),('let args=&(new,);let sk=a.sharing_config.key();','let args=&(new,);')]
H['hBC']=[('let a=&ctx.accounts;let mint=a.mint.key();','let a=&ctx.accounts;let mint=a.mint.key();let bc=&a.bonding_curve;'),('==a.bonding_curve.creator&&','==bc.creator&&')]
H['hIF']=[('let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();','let shared=if a.sharing_config.key()==a.bonding_curve.creator{a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty()}else{false};')]
H['hQL']=[(_S+_QL,_QL+_S)]
H['hMint']=[('let a=&ctx.accounts;let mint=a.mint.key();'+_H,'let a=&ctx.accounts;let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",a.mint.key().as_ref()],&crate::ID);holder_key=hk.0;let mint=a.mint.key();')]
_M='let a=&ctx.accounts;let mint=a.mint.key();'
H['hHold']=[(_M,_M+'let hb=holder==Some(true);'),('let hopt=holder;let holder=hopt==Some(true);','let hopt=holder;let holder=hb;')]
H['hCb']=[(_M,_M+'let cbe=a.bonding_curve.is_cashback_coin;'),('cashback:a.bonding_curve.is_cashback_coin,','cashback:cbe,')]
H['hMay']=[(_M,_M+'let mye=a.bonding_curve.is_mayhem_mode;'),('mayhem:a.bonding_curve.is_mayhem_mode,','mayhem:mye,')]
H['hHr']=[(_M,_M+'let hre=a.bonding_curve.is_holder_reward;'),('holder_reward:a.bonding_curve.is_holder_reward,','holder_reward:hre,')]
H['hHoldE']=[('let hopt=holder;let holder=hopt==Some(true);','let hopt=holder;let holder=matches!(hopt,Some(true));')]
def edits(name):
    gs=name.split('+'); E=[]
    if gs[0]=='nopda': gs=gs[1:]
    else: E+=gen.G['pda']
    for g in gs:
        if g in ('pda',''): continue
        E+=H[g] if g in H else [tuple(x) for x in P[g]]
    return E
