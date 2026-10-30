import struct
import unittest
from coords import sites, orig_sites
from test_coords_bounds import CoordinateBoundsTests


def instruction(op, regs=0, offset=0, immediate=0):
    return struct.pack('<BBhi',op,regs,offset,immediate)


class CoordinateCallTests(unittest.TestCase):
    path = b'programs/pump/src/example.rs'
    sections = {'.rodata':{'addr':0x2000,'offset':0,'size':len(path)}}

    def descriptor(self, register, call=None, reload=False):
        pointer = instruction(0x18,register,immediate=0x2000)+bytes(8)
        raw = pointer
        if call is not None: raw += instruction(call,0x10 if call == 0x85 else 0,immediate=1)
        if reload: raw += pointer
        return raw+instruction(0x7b,(register<<4)|10,-16)+instruction(0x7a,10,-8,len(self.path))+instruction(0x62,10,0,42)

    def test_pre_call_scratch_pointer_is_not_recovered(self):
        for call in (0x85,0x8d):
            for register in range(1,6):
                with self.subTest(call=call,register=register):
                    self.assertEqual(sites(self.path,self.sections,0,self.descriptor(register,call)),[])

    def test_preserved_registers_and_post_call_reload_still_recover(self):
        for register,call,reload in [(6,0x85,False),(9,0x8d,False),(1,0x85,True),(5,0x8d,True),(1,None,False)]:
            with self.subTest(register=register,call=call,reload=reload):
                result = sites(self.path,self.sections,0,self.descriptor(register,call,reload))
                self.assertEqual(len(result),1)
                self.assertEqual(result[0]['path'],self.path.decode())
                self.assertEqual(result[0]['line'],42)

    def test_retained_reused_descriptors_keep_their_coordinates(self):
        result = {site['slot']:site for site in orig_sites(0x18678)}
        for slot,line in ((4296,466),(4520,493)):
            self.assertEqual(result[slot]['line'],line)
            self.assertEqual(result[slot]['path'],'programs/pump/src/create_v2.rs')


if __name__ == '__main__': unittest.main()
