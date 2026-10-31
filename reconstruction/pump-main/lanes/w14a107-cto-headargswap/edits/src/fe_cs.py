EDITS=[('if let Some(f)=fee{curve.creator_fee_bps=f;}', 'if fee.is_some(){curve.creator_fee_bps=fee.unwrap();}')]
