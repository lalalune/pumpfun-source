# Round-3 genes: peer evidence (#2564 errseq: holder `& 1`, 306 tag test `& 1`, shared test inside
# validate's non-holder arm) plus 298/306 Option forms.
import importlib.util, os
_s = importlib.util.spec_from_file_location('g2', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'genes2.py'))
_g2 = importlib.util.module_from_spec(_s); _s.loader.exec_module(_g2)
GENES = dict(_g2.GENES)
L306 = "  let Some(t)=new else{return Err(error!(PumpError::CtoNewCreatorRequired));};"
GENES.update({
    'validate_shared_arm': [("fn validate(st:&CtoState,holder:bool,", "fn validate(st:&CtoState,shared:bool,holder:bool,"),
                            ("if t==holder_key||t==sharing{return Err(error!(PumpError::InvalidCreator));}t};", "if t==holder_key||t==sharing{return Err(error!(PumpError::InvalidCreator));}if shared{st.creator}else{t}};"),
                            ("validate(&st,holder,", "validate(&st,shared,holder,"),
                            ("if shared&&!holder{target=st.creator;}", "")],
    'validate_shared_arm2': [("fn validate(st:&CtoState,holder:bool,", "fn validate(st:&CtoState,shared:bool,holder:bool,"),
                            ("if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}t};", "if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}if shared{st.creator}else{t}};"),
                            ("validate(&st,holder,", "validate(&st,shared,holder,"),
                            ("if shared&&!holder{target=st.creator;}", "")],
    'to_ifexpr2': [("let mut target=validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key())?;", "let target=validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key())?;"), ("if shared&&!holder{target=st.creator;}", "let target=if shared&&!holder{st.creator}else{target};")],
    'sharing_key_once': [("let mut target=validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key())?;", "let mut target=validate(&st,holder,fee,new,&holder_key,a.sharing_config.key)?;")],
    'n306_match': [(L306, "  let t=match new{Some(t)=>t,None=>return Err(error!(PumpError::CtoNewCreatorRequired))};")],
    'n306_isnone': [(L306, "  if new.is_none(){return Err(error!(PumpError::CtoNewCreatorRequired));}let t=new.unwrap();")],
    'n306_okorelse': [(L306, "  let t=new.ok_or_else(||error!(PumpError::CtoNewCreatorRequired))?;")],
    'n306_iflet': [(L306, "  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};")],
    'n298_iflet': [("if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}", "if let Some(_)=new{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}")],
    'n298_notnone': [("if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}", "if !new.is_none(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}")],
    'holder_unwrap_param': [("let holder=holder==Some(true);", "let holder=holder.unwrap_or_default();")],
    'holder_iflet': [("let holder=holder==Some(true);", "let holder=if let Some(h)=holder{h}else{false};")],
    'holder_match': [("let holder=holder==Some(true);", "let holder=match holder{Some(h)=>h,None=>false};")],
})
