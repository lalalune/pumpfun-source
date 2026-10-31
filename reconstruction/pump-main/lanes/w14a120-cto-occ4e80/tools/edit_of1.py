# old_fee read before the sharing CPI match (old value; the pump_fees CPI cannot write the pump-owned curve)
EDITS=[(" match sharing_update{Some(val)=>{"," let old_fee=a.bonding_curve.creator_fee_bps;match sharing_update{Some(val)=>{"),
       ("let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;","let old_creator=curve.creator;"),
       (" let (old_creator,old_fee)={"," let old_creator={"),(" (old_creator,old_fee)};"," old_creator};")]
