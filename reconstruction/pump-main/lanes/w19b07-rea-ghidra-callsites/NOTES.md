# w19b07-rea-ghidra-callsites: fill reads moved by the inter-call jump model

Target `0x22a10` `admin_cto::execute`. Three `holder_key` fill reads move out of the line 312 error block: one to the sweep gate (line
647), two to the 648 error path. Bytes stay 27,400. Six aligned jumps in W1/S1 get the original's displacement; three J2 jumps lose it.

Tables and tools (inter-call gap table, `jmove.py`, `fill.py`): `origin/swarm/w19b07-rea-ghidra-callsites`.
