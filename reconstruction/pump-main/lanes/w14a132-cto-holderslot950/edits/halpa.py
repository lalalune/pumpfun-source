import os
W=os.environ.get('HW','i8')
EDITS=[("  %685 = icmp ne i8 %684, 0\n","  %hl2 = load "+W+", ptr %hslot\n  %685 = trunc "+W+" %hl2 to i1\n")]
