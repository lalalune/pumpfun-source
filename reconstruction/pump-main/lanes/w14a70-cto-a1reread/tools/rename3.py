import sys,os,struct
# rename.py: naming-fix bound on a1 fn.bin: swap r6/r8 roles in the token arm and drop the spill+mov (shift.py model)
D=os.path.dirname(os.path.abspath(__file__)); G={'__name__':'lib','__file__':D+'/shift.py'}
sys.argv=['shift.py',sys.argv[1]]; exec(open(D+'/shift.py').read(),G)
ins=G['ins']; slot=G['slot']
def at(off): return slot.index(off//8)
def setreg(off,dst=None,src=None):
    b=ins[at(off)]
    if dst is not None: b[1]=(b[1]&0xf0)|dst
    if src is not None: b[1]=(b[1]&0x0f)|(src<<4)
def show(off): b=ins[at(off)]; print(hex(off),b.hex())
for o in (0x20a0,0x20a0,0x20a8,0x20b0,0x20b8,0x2110,0x5e50,0x6028,0x6088): show(o)
setreg(0x20b0,dst=8); setreg(0x20b8,dst=6); setreg(0x20c0,src=8); setreg(0x2118,dst=6); setreg(0x5e50,dst=6); setreg(0x6028,src=6); setreg(0x6088,src=8)
base=G['M'](G['build']()); print('renamed M',base)
# drop the two extra insns one at a time (build handles one delete)
d1=at(0x20a0); c=G['build'](None,d1); open(D+'/ren1.bin','wb').write(c)
G2={'__name__':'lib','__file__':D+'/shift.py'}; sys.argv=['shift.py',D+'/ren1.bin']; exec(open(D+'/shift.py').read(),G2)
d2=G2['slot'].index(0x20a0//8); c2=G2['build'](None,d2); open(D+'/ren2.bin','wb').write(c2); print('renamed-2insn M',G2['M'](c2),len(c2))
