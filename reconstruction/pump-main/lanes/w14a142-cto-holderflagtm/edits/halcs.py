import os
W=os.environ.get('HW','i8')
EDITS=[("  %582 = and i8 %0, 1\n","  %hl1 = load "+W+", ptr %hslot\n"+("  %582 = trunc "+W+" %hl1 to i8\n" if W!='i8' else "  %582 = or i8 %hl1, 0\n"))]
