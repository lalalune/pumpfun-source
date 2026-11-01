# w19a04-shim-nat-ra1st: sweep exits in the original's shape

Target `0x22a10` `admin_cto::execute`, 27,400 B. Tools and the RA first-divergence debugger are on `origin/swarm/w19a04-shim-nat-ra1st`.

An RA first-divergence walk on the natural base showed the tag and payload colours (original r7/r9) and most of T1 hang on one fact: the sweep's exits. The original's sweep:

- native arm: `return (if amount>0{ensure?;transfer_native(..)}else{Ok(())}).map(|()|amount);` all exits reach the join J at 0x3c58;
- token arm, frozen and zero amount: `return Ok(amount);`, so they share the `?` exit chain (J), as `jeq r6,0,0x3c58` shows;
- token arm, CPI path: `create_idempotent(..)?;transfer_vault_tokens(..)?;` then the tail `Ok(amount)`, which threads straight to the post-sweep block (0x60d8 `mov r9,r6; ..; ja 0x3c68`), with separate Err blocks 0x6380 and 0x63a8.

J stays one block right before the post-sweep block, so it falls through and the tail-duplicated copies at 0x24a0 and 0x2608 keep their `ja`. Two `read_volatile` placeholders repay the pin.
