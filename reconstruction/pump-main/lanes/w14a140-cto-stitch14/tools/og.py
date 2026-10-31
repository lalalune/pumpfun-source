# w14a123 origfill genes: (old,new) exact single-occurrence replacements in admin_cto.rs (line count kept)
G={}
_HA="if holder{(false,Some(None),false)}"
G['ha']=[(_HA,"if holder{(false,Some(args.0),false)}")]
G['hn']=[(_HA,"if holder{(false,Some(new),false)}")]
_T1="let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r"
G['t1']=[(_T1,"let r=(false,Some(args.0),true);target=st.creator;r")]
G['su1']=[("if holder{(false,Some(None),false)}else{let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r}",
           "let r=(false,Some(args.0),!holder);if !holder{target=a.bonding_curve.creator;}r")]
G['su2']=[("if holder{(false,Some(None),false)}else{let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r}",
           "if !holder{target=a.bonding_curve.creator;}(false,Some(args.0),!holder)")]
_SIG=(",sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);",",sharing:&Pubkey,shared:bool)->Result<(Pubkey,bool,Option<Option<Pubkey>>,bool)>{let holder=hopt==Some(true);")
_RET=(" Ok(target)}pub fn execute"," Ok((target,collect_old,sharing_update,skip))}pub fn execute")
_EX=("let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};",
     "let sk=a.sharing_config.key();let (target,collect_old,sharing_update,skip)=validate(&st,hopt,fee,new,&holder_key,&sk,shared)?;")
_CB="let cashback=if holder{false}else{st.cashback};\n\n"
def _vin(tree): return [_SIG,_RET,_EX,(_CB,"let cashback=if holder{false}else{st.cashback};\n "+tree+"\n")]
G['vin']=_vin("let (target,collect_old,sharing_update,skip)=if shared{if holder{(target,false,Some(None),false)}else{(st.creator,false,Some(new),true)}}else{(target,!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};")
G['vinh']=_vin("let (target,collect_old,sharing_update,skip)=if shared{if holder{(target,false,Some(new),false)}else{(st.creator,false,Some(new),true)}}else{(target,!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};")
G['vinm']=_vin("let (target,collect_old,sharing_update,skip)=if !shared{(target,!st.holder_reward&&st.creator!=Pubkey::default(),None,true)}else if holder{(target,false,Some(None),false)}else{(st.creator,false,Some(new),true)};")
# tree placed inside the target if: holder arm / else arm carry the shared override (per-arm, before cashback)
