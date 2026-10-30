import runpy; EDITS=runpy.run_path('se/s8.py')['EDITS']+[("if let Some(f)=fee{curve.creator_fee_bps=f;}","curve.creator_fee_bps=fee.unwrap_or(curve.creator_fee_bps);")]
