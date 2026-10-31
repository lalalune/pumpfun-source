import json,subprocess,sys
L='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a20-cto-ovarmpin/reconstruction/pump-main/log_attempt.py'
LANE='w15a20-cto-ovarmpin'; M='86e2a6b'
B=' raw-IR capture + rx opt/llc oracle on main 86e2a6b (m0 eq_main, 0.67376 @27400, true-LCS ---2255 rfj3007).'
R=[
('mech-analysis','analyzed','ov-family hoist of the sharing_update CPI arm: which pass moves it (step 1)',
 'NOT IR jump threading/simplifycfg: post-O3 IR block order is the same (admin_cto_sharing_config block idx 250 m0 vs 253 ov1a; bb56.i sweep-join IR identical). It is MachineBlockPlacement after a branch-folder tail-merge split of the post-sweep Result join bb56.i (w14a142 mechanism): in ov1a greedy carries the sharing_update tag ([r10-2272]) in r5 across the join (6 preds reload r5=[-2272], 3 preds COPY r5<-r6), bb56.i gains live-in r5, splits in two, the to_string error pred falls into the 5-pred half and chunk B (bb56.i,bb88,bb35, sharing arm, tail) is placed at 0x2458 ahead of the sweep body. ov2 does the same with r9=[-2400]. -enable-tail-merge=false hoists main too.'),
('ov1a-restore','analyzed','MIR join-restore oracle on ov1a (r5 COPY r6 -> reload [-2272] in bb82.i/bb16.i/bb93.i, stop/start-before branch-folder)',
 'arm back to 0x4a48 (main 0x4a20); ov1a 0.52838 @27408; true-LCS rfj -13 (base -534), rf- -32, --- -313: placement loss fully recovered, ov1a still below main'),
('ov2-restore','analyzed','MIR join-restore oracle on ov2 (drop r9 defs in 5 join preds, reload r9=[-2400] at bb78 head)',
 'arm back; 0.41724 @27640; rfj -38 (base -541): validate 1000:+11 but 0x1800 -23, 0x3000 -14'),
('m_sl','rejected','sharing_update computed after the sweep from shared/_holder/new (tree and Ok hop drop it), on main','0.38587 @27440, arm hoisted 0x3228, rfj -547'),
('o_sl','rejected','ov1a + sharing_update after sweep','0.39708 @27624, hoisted, rfj -545'),
('m_rs','rejected','event sharing_config_reset:shared (k_ev_reset_shared) on main, re-priced','0.59081 @27288, arm kept 0x4a10, rfj -19 (--- -212)'),
('o_rs','rejected','ov1a + event sharing_config_reset:shared: the ordinary carrier that keeps the sharing arm at main position','arm kept 0x4a28 (no tag live-in at bb56.i); 0.52042 @27272; rfj -26 (validate 1000:+3)'),
('m_il','rejected','match sharing_update -> if let Some(val)=sharing_update on main','0.67236 @27392, rfj +0, --- -5'),
('o_il','rejected','ov1a + if let sharing match','0.42658 @27440, hoisted 0x3280, rfj -534'),
('m_sr','rejected','m_sl + reset:shared on main','0.3994 @27392, hoisted, rfj -545'),
('o_sr','rejected','ov1a + m_sl + reset:shared','0.39169 @27544, hoisted, rfj -541'),
('ov1_rs','rejected','ov1 (validate shared override, tree no longer assigns target) + reset:shared','arm kept 0x49b0; 0.52671 @27152; rfj -31'),
('ov2_rs','rejected','ov2 (whole tree in validate arms) + reset:shared','arm kept 0x4a90; 0.41204 @27424; rfj -51 (1000:+11, 1800:-26)'),
('jt-threshold','analyzed','opt -jump-threading-threshold oracle: second JT on execute refuses thread-through-two-blocks bb75->bb18/bb21 (PredBB cost 8>6) because bb75 holds 10 memcpys of the 7/9 B target chain target.i->_49->_411->_48->val->target',
 'threshold 20: JT threads bb75+bb18/bb21 (per-arm holder/shared tree tests, class F shape); m0 0.50821 @27576 rfj -49 (validate 800:+3 1800:+6, 0x4800 -44); ov1 -45, ov1a -39, o_rs -15, m_rs -17: threading alone is worth <= +9 validate tokens'),
('lv3','rejected','w13a18 lv3 faithful out-param form ported to 86e2a6b (validate(..,hb,shared,..,out:&mut Pubkey)->Result<Pubkey>, Ok(*holder_key), tree no override)','0.21547 @27456, hoisted 0x33b0, rfj -503'),
('vb','rejected','w13a18 vb out-param form (Result<()>) ported to 86e2a6b','in-pipeline JT threads bb76+bb18, bb49.i+bb76 (original three-way fee-None threading); arm kept 0x4b60; 0.2419 @27104; rfj -114 (validate flat, 0x5000-0x6400 -90)'),
('lv3_rs','rejected','lv3 + reset:shared','0.24727 @27376, still hoisted, rfj -502'),
('vb_rs','rejected','vb + reset:shared','0.27543 @27088, rfj -116'),
]
for k,st,h,n in R:
    key=f'0x22a10-w15-{M}-ovarmpin-{k}-v1'
    d={'normalized':1034,'raw':1034,'losses':[],'raw_losses':[],'notes':n+'.'+B}
    r=subprocess.run(['python3',L,'record','--lane',LANE,'--approach','ovarmpin','--target','0x22a10','--dedupe-key',key,'--hypothesis','ovarmpin '+h,'--status',st,'--data',json.dumps(d)],capture_output=True,text=True)
    print(k,r.returncode,r.stdout[-80:].strip(),r.stderr[-200:])
