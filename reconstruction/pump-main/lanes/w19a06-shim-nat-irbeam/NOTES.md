# w19a06-shim-nat-irbeam

Target `0x22a10` `admin_cto::execute`. Tools and tables are on `origin/swarm/w19a06-shim-nat-irbeam`.

This landing, on main 18d76df37 (0.87092): the `dk` form of the sweep `dest` (w19a07), with `dest` in a `MaybeUninit` of the `then` closure, so `lifetime.end(dest)` leaves the sweep exit tails. +35 M at the pin.
