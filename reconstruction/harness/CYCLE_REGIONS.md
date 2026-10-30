# Cyclic control-flow regions

`control_flow.py` reports `cyclic_regions`: strongly connected components with
multiple blocks or a self edge, using only decoded internal CFG edges. Each row
lists sorted function-relative block offsets, entry blocks with incoming edges
from outside the component (including function entry), and entry reachability.

This groups repeated control flow for reconstruction experiments. Nested loops
may form one component. These are not natural-loop headers or dynamic iteration
counts; unreachable cycles are retained, calls are not traversed, and existing
branch diagnostics still apply. Scorer acceptance and program bytes are unchanged.
The traversal is iterative so large CFGs do not depend on Python recursion limits.
