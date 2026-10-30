NF="let nf=a.bonding_curve.creator_fee_bps;"
EVNF="new_creator_fee_bps:nf,"
PA="let pargs=(target,a.bonding_curve.is_holder_reward,fee);"
EVHR="is_holder_reward:holder,"
EVCB="is_cashback_coin:a.bonding_curve.is_cashback_coin,"
EVNC="new_creator:a.bonding_curve.creator,"
def mk(nf_inline=False,pa_hold=False,ev_hr_curve=False,ev_cb_hold=False):
    E=[]
    if nf_inline: E+=[(NF,''),(EVNF,'new_creator_fee_bps:a.bonding_curve.creator_fee_bps,')]
    if pa_hold: E+=[(PA,'let pargs=(target,holder,fee);')]
    if ev_hr_curve: E+=[(EVHR,'is_holder_reward:a.bonding_curve.is_holder_reward,')]
    if ev_cb_hold: E+=[(EVCB,'is_cashback_coin:cashback,')]
    return E
