import runpy,os
E=runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)),'vb01v.py'))['EDITS']
EDITS=E+[("let (target,sharing_update,cashback)=Ok::<_,anchor_lang::error::Error>((target,sharing_update,cashback))?;","let target=Ok::<_,anchor_lang::error::Error>(target)?;")]
