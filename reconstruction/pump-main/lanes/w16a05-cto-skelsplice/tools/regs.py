# Sub-regions of the ORIGINAL admin_cto::execute window (byte offsets from 0x22a10), per the w16 skeleton panel.
R=[(0x0000,0x0280,'entry.pda'),     # holder PDA + shared test
   (0x0280,0x0420,'entry.ql'),      # quote_locked (default/native/whitelist)
   (0x0420,0x0700,'entry.st'),      # CtoState + new copy + key copies, mayhem/284
   (0x0700,0x0b00,'holder_head'),   # validate holder arm head, 289/298 sites
   (0x0b00,0x0e60,'nonholder'),     # non-holder arm 307/312 memcmps + shared split
   (0x0e60,0x1258,'e306_296_326'),  # 306/296/326 error blocks + holder exit
   (0x1258,0x1490,'e312_307'),      # 312/307 error blocks (to_string)
   (0x1490,0x1800,'fee_chain'),     # fee checks 330/334/338
   (0x1800,0x1c00,'join'),          # per-arm exits, tuple/target, prepare_bonding_curve, 410
   (0x1c00,0x2600,'sweep_head'),
   (0x2600,0x3c00,'tcf'),
   (0x3c00,0x4a00,'sharing_cpi'),
   (0x4a00,0x5400,'tail_hot'),      # sharing call, curve store, pool CPI, Clock, event
   (0x5400,0x5a00,'cold_err'),      # cold error exits, native Rent
   (0x5a00,0x6c00,'wallet')]        # native transfer, wallet arm (collect, coin CPI)
def reg(o):
    for lo,hi,n in R:
        if lo<=o<hi: return n
    return '?'
