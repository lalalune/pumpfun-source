G={}
_H="->Result<Pubkey>{let holder=hopt==Some(true);"
G['v_uo']=[(_H,"->Result<Pubkey>{let holder=hopt.unwrap_or(false);")]
G['v_mt']=[(_H,"->Result<Pubkey>{let holder=matches!(hopt,Some(true));")]
G['v_ud']=[(_H,"->Result<Pubkey>{let holder=hopt.unwrap_or_default();")]
G['v_isa']=[(_H,"->Result<Pubkey>{let holder=hopt.is_some_and(|h|h);")]
G['nop']=[]
_A="let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"
G['a_after']=[(_A,"let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let args=&(new,);")]
G['a_none']=[(_A,"let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"),("let r=(false,Some(args.0),true);","let r=(false,Some(new),true);")]
G['a_inarm']=[(_A,"let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"),("let r=(false,Some(args.0),true);","let args=&(new,);let r=(false,Some(args.0),true);")]
G['a_val']=[(_A,"let args=(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;")]
G['a_top']=[(_A,"let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"),("let hopt=holder;let holder=hopt==Some(true);","let args=&(new,);let hopt=holder;let holder=hopt==Some(true);")]
