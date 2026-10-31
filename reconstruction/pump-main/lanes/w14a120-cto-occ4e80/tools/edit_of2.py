# old_creator and old_fee read before the sharing CPI match
EDITS=[(" match sharing_update{Some(val)=>{"," let (old_creator,old_fee)=(a.bonding_curve.creator,a.bonding_curve.creator_fee_bps);match sharing_update{Some(val)=>{"),
       ("let old_creator=curve.creator;let old_fee=curve.creator_fee_bps;",""),
       (" let (old_creator,old_fee)={"," {"),(" (old_creator,old_fee)};"," };")]
