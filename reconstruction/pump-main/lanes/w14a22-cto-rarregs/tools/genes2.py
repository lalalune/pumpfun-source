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
