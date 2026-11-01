# w19a07-cto-nat-sweepexit: natural base with the original's sweep exit

Target `0x22a10` `admin_cto::execute`, 27,400 B. Source is natstitch n2 (shim-free f17 + early `sharing_update`), w19a08's Some(None) copy, and three sweep forms:
the native tail `if amount>0{ensure?;transfer_native(..).map(|()|amount)}else{Ok(0)}`, `Rent::get` hoisted into its own native test with `let amount;` between, and `dest` as a `MaybeUninit` local of the `then` closure.
Together they give the original's sweep exit CFG, one payload class in r9 and tag in r7. Two holder_key byte reads repay 8 B each to the pin. Tools and tables: `origin/swarm/w19a07-cto-nat-sweepexit`.
