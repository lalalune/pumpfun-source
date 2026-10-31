# pool_updated as the value of the pool-CPI if (true after the CPI, false after msg); pargs inside the arm
EDITS=[("let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;let pargs=(target,a.bonding_curve.is_holder_reward,fee);\n if pool_updated{",
        "\n let pool_updated=if !a.pool.data_is_empty() && a.pool.owner==&AMM{let pargs=(target,a.bonding_curve.is_holder_reward,fee);"),
       ("signer_seeds),pargs.0,pargs.1,pargs.2)?;\n }else{msg!(\"No canonical pump pool for this mint; curve only\");}",
        "signer_seeds),pargs.0,pargs.1,pargs.2)?;true\n }else{msg!(\"No canonical pump pool for this mint; curve only\");false};")]
