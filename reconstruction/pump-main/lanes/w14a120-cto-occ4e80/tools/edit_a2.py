# pool_updated as the value of the pool-CPI if; pargs before the if (after the gate reads in source order kept: pargs first)
EDITS=[("let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;let pargs=(target,a.bonding_curve.is_holder_reward,fee);\n if pool_updated{",
        "let pargs=(target,a.bonding_curve.is_holder_reward,fee);\n let pool_updated=if !a.pool.data_is_empty() && a.pool.owner==&AMM{"),
       ("signer_seeds),pargs.0,pargs.1,pargs.2)?;\n }else{msg!(\"No canonical pump pool for this mint; curve only\");}",
        "signer_seeds),pargs.0,pargs.1,pargs.2)?;true\n }else{msg!(\"No canonical pump pool for this mint; curve only\");false};")]
