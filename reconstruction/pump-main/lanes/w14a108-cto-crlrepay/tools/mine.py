G={}
_H="->Result<Pubkey>{let holder=hopt==Some(true);"
G['v_uo']=[(_H,"->Result<Pubkey>{let holder=hopt.unwrap_or(false);")]
G['v_uo289']=G['v_uo']+[("&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}","&&!holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}")]
G['v_mt']=[(_H,"->Result<Pubkey>{let holder=matches!(hopt,Some(true));")]
G['v_ud']=[(_H,"->Result<Pubkey>{let holder=hopt.unwrap_or_default();")]
G['v_isa']=[(_H,"->Result<Pubkey>{let holder=hopt.is_some_and(|h|h);")]
G['v_289h']=[("&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}","&&!holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}")]
_V="unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};"
G['dv334']=[(_V+"if !st.fee_configurable","if !st.fee_configurable")]
G['dv338']=[("PumpError::CreatorFeeBpsOutOfRange));}"+_V+"}None=>{}}","PumpError::CreatorFeeBpsOutOfRange));}}None=>{}}")]
G['dvb']=G['dv334']+G['dv338']
import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import extra87
G['t1']=extra87.X['t1']; G['a1']=extra87.X['a1']
_SH='a.sharing_config.key()==a.bonding_curve.creator&&'
G['cs']=[(_SH,'a.bonding_curve.creator==a.sharing_config.key()&&')]
G['cs_eq']=[(_SH,'a.bonding_curve.creator.eq(&a.sharing_config.key())&&')]
G['cs_blk']=[(_SH,'{let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&')]
G['cs_ref']=[(_SH,'&a.bonding_curve.creator==&a.sharing_config.key()&&')]
G['cs_blk2']=[(_SH,'{let sk=a.sharing_config.key();sk==a.bonding_curve.creator}&&')]
G['cs_hoist']=[('let shared='+_SH,'let sk=a.sharing_config.key();let shared=a.bonding_curve.creator==sk&&'),('let sk=a.sharing_config.key();let mut target=validate','let mut target=validate')]
G['cs_blkc']=[(_SH,'{let sk=a.sharing_config.key();let cr=&a.bonding_curve.creator;*cr==sk}&&')]
G['cs_blkp']=[(_SH,'{let sk:Pubkey=a.sharing_config.key();a.bonding_curve.creator==sk}&&')]
