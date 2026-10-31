import runpy,json
g=runpy.run_path('common.py'); globals().update({k:v for k,v in g.items() if k.isupper()})
d=json.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))
s=open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a23-cto-decisionenum/programs/pump/src/creator/admin_cto.rs').read()
MIL=[(SH0," if let Some(val)=sharing_update{\n"),(SH1," }\n")]
open('mil.py','w').write('EDITS='+repr(MIL)+'\n')
names=[]
for k in d['knobs']:
  ed=k.get('edit') or []
  if k['name'] in ('L_share_none_first','ev_ts_presig','s_dest_borrow','s_old_borrow','g_s7_dborrow','p_ev_ts_last','w_create_rev'): continue
  if ed and all(s.count(e['old'])==1 for e in ed) and all(e['old'].count('\n')==e['new'].count('\n') for e in ed):
    E=[(e['old'],e['new']) for e in ed]
    if any(a in (SH0,SH1) or SH0 in a or SH1 in a for a,_ in E): continue
    n='mk_'+k['name']; open(n+'.py','w').write('EDITS='+repr(MIL+E)+'\n'); names.append(n)
print(' '.join('e/'+n+'.py' for n in names))
