exec(open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a31-cto-lv3relayout/e/s_map.py').read())
EDITS=EDITS+[('  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};', '  let t=new.ok_or_else(||error!(PumpError::CtoNewCreatorRequired))?;')]
