import json,os
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a15-cto-tcfprofile')
D='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w16a15-cto-tcfprofile/reconstruction/pump-main/lanes/w16a15-cto-tcfprofile'
S=json.load(open(OUT+'/an/singles.json')); b=json.load(open(OUT+'/an/beam.json'))
ok=[r for r in S if 'M' in r]
summ={
 'lane':'w16a15-cto-tcfprofile','wave':16,'target':'0x22a10 admin_cto::execute','file':'programs/pump/src/creator/admin_cto.rs',
 'base':{'main':'599891304 (admin_cto = 1f4e396b5)','ratio':0.67436,'slots_diff':3141,'bytes':27400,'M':2251,'normalized':1034,'raw':1034},
 'best':{'ratio':0.67436,'slots_diff':3141,'bytes':27400,'note':'main; no zero-loss improvement found'},
 'landed':False,'pr':3881,
 'result':'kill (notes): no composite fixes >=6 abort jumps without losing M; c2 marker absent in all captured spellings',
 'captures':len(ok),'compile_errors':sum(1 for r in S if 'error' in r),
 'abort_profile_main':{'jumps':41,'right':11,'tcf_right':7,'sharing_right':4,
   'cum':[8,8,8,0,0,-8,-8,0,0,-8,-8,0,0,8,8,0,32,32,8,16,32,32,24,40,40,0,0,0,0,40,40,24,24,16,24,-56,-64,-80,-80,-104,-40]},
 'joint_search':{'method':'beam 5000 over one spelling per literal group, additive model (= splice, = real captures for 6 composites)',
   'best_predicted':b['top'][0],'levels':b['levels']},
 'mechanisms':[
   'The 0x26e0 abort block is the target of 41 jumps (25 TCF + 16 sharing-CPI clone checks); main has 11 right.',
   'All non-Rc instructions in the TCF run are greedy spill code; the +-8 per-clone rhythm is single spills of held values.',
   '13 of 18 wrong TCF jumps have odd drift (8 B units); every cheap literal lever is an even (+-16) move, so it cannot fix them.',
   'Odd moves come only with whole-run RA reshuffles (H:KLDORSWE, T5, T8, T*:LKDORSWE, P:KRSWELDO) costing 50-220 M, or -8 B re-read removals that lose the 4 sharing jumps.',
   'c2 tax: r6 over the run is held by %1726 = accounts+264 (&holder_creator_vault) region-split piece; the bump %2048 holds r9; so accounts+232 takes r0 (orig r6) and the flag temps lose r0. Upstream head fact bounded by w15a07 (#3651).'],
 'rejected':[r['name']+' '+str(r.get('genes'))+' M '+str(r['M']) for r in ok if r['name']!='main'][:120],
 'unresolved':['the original spill-at-def of &holder_creator_vault and the bump (head fact)','sharing-run drift (seg29 +40, seg35 -80, seg40 +64) from global/authority flag-copy placement'],
 'next_ideas':['a sweep-head source form whose greedy order spills accounts+264 and the bump at definition (frees r6/r9 for the run); w15a07 bounded the IR re-derivations, not greedy-order levers',
   'sharing-run profile: b2/b3 literal joint search with the same beam tool (seg29/35/40 dominate the 12 wrong sharing jumps)',
   'use case-unique capture names on macOS (rx/ and ir/ collide case-insensitively)'],
 'tools':['tools/prof.py','tools/census.py','tools/mk.py','tools/beam.py','tools/genes_tp.py','tools/tcfsplice.py','tools/scanprof.py','tools/scane8.py','tools/mktable.py','tools/dbgocc.py'],
 'ledger':{'approach':'tcfprofile','keys':'0x22a10-w16-1f4e396-tcfprofile-<cell>-v1'}}
json.dump(summ,open(D+'/SUMMARY.json','w'),indent=1); print('ok',len(ok))
