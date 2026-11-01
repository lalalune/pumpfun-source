import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import revidiom
R=[("Q1 sharing-CPI clone run (accounts ptr reloaded per clone)",0x3d88,0x4638),
   ("Q1 TCF clone reloads",0x3200,0x3360),
   ("Q2 entry: new pieces tag+7/8/8/8/1",0x4d8,0x540),
   ("Q2 sharing-CPI val copy (tag + 7/8/8/8/1)",0x3d20,0x3d88),
   ("Q2 non-holder arm: t rebuilt from pieces before memcmp",0xc08,0xc80),
   ("Q2 holder arm: target pieces",0x1138,0x1180),
   ("Q2 validate exit: target pieces from new",0x1850,0x1898),
   ("Q2 after validate: target final copy",0x19c0,0x1a30),
   ("Q3-B curve bools and Global ptr loaded early and held",0x140,0x2b8),
   ("Q3-F per-arm phi constants",0xd78,0xe60),
   ("Q3-H holder and-1 in r8, jeq+1;ja pairs",0x5d8,0x750),
   ("Q3-b01 by-value key copies",0x540,0x5d8),
   ("Q4 validate fee OK block (334/338 placeholders)",0x1700,0x17b0)]
for name,lo,hi in R:
    print(f'#### {name}'); revidiom.lookup(lo,hi,4,5); sys.stdout.flush()
