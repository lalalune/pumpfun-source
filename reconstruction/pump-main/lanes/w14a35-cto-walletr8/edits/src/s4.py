EDITS=[("if let Some((collected,quote_mint))=crate::collect_v2::collect(","if let Some((collected,quote_mint))=match crate::collect_v2::collect("),
("a.system_program.as_ref())?{\n","a.system_program.as_ref()){Ok(v)=>v,Err(e)=>return Err(e)}{\n")]
