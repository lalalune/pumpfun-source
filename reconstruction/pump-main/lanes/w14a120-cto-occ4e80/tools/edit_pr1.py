# pool_updated re-evaluated at the event (gate kept for the if)
EDITS=[("let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;","let gate=!a.pool.data_is_empty() && a.pool.owner==&AMM;"),
       ("\n if pool_updated{\n","\n if gate{\n"),
       ("swept_to_holder_vault:swept,pool_updated};","swept_to_holder_vault:swept,pool_updated:!a.pool.data_is_empty() && a.pool.owner==&AMM};")]
