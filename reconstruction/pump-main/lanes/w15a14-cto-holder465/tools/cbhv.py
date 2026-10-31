EDITS=[("let holder=hopt==Some(true);let cashback=!holder&&st.cashback;let args=","let holder=hopt==Some(true);let cashback=st.cashback;let args="),
       ("  curve.is_cashback_coin=cashback;\n","  curve.is_cashback_coin=cashback&&!holder.unwrap_or(false);\n")]
HYP="block cashback=st.cashback (carried in the tuple), curve.is_cashback_coin=cashback&&!holder.unwrap_or(false) (!holder recomputed at the store)"
