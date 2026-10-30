import re
def T(s):
    s=s.replace("let pargs=(target,a.bonding_curve.is_holder_reward,fee);","let pargs=(swept,target,a.bonding_curve.is_holder_reward,fee);",1)
    s=re.sub(r"pargs\.([0-2])\b",lambda m:"pargs.%d"%(int(m.group(1))+1),s)
    assert s.count("swept_to_holder_vault:swept")==1
    return s.replace("swept_to_holder_vault:swept","swept_to_holder_vault:pargs.0")
EDITS=[]
