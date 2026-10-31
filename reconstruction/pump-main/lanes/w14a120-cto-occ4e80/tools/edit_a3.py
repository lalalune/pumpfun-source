# pool_updated as a match on the gate bool: match gate{true=>{cpi?;true},false=>{msg;false}}
EDITS=[("let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;let pargs=(target,a.bonding_curve.is_holder_reward,fee);\n if pool_updated{",
        "let gate=!a.pool.data_is_empty() && a.pool.owner==&AMM;let pargs=(target,a.bonding_curve.is_holder_reward,fee);\n let pool_updated=match gate{true=>{"),
       ("signer_seeds),pargs.0,pargs.1,pargs.2)?;\n }else{msg!(\"No canonical pump pool for this mint; curve only\");}",
        "signer_seeds),pargs.0,pargs.1,pargs.2)?;true\n }false=>{msg!(\"No canonical pump pool for this mint; curve only\");false}};")]
