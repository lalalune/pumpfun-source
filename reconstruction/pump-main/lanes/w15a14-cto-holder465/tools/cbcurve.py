EDITS=[("  curve.is_cashback_coin=cashback;\n","  curve.is_cashback_coin=!holder.unwrap_or(false)&&curve.is_cashback_coin;let _=cashback;\n")]
HYP="curve.is_cashback_coin=!holder.unwrap_or(false)&&curve.is_cashback_coin (state re-derived at the curve store; no head cashback)"
