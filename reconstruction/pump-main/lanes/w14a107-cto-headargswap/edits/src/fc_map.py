EDITS=[('if let Some(f)=fee{curve.creator_fee_bps=f;}', 'curve.creator_fee_bps=fee.map_or(old_fee,|f|f);')]
