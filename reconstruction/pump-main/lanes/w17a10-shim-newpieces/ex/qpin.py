import runpy
D='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a10-shim-newpieces/ex/'
Q=('  %105 = getelementptr inbounds i8, ptr %st, i64 43\n  %106 = load i8, ptr %105, align 1, !range !4, !noundef !2\n',
   '  %105 = getelementptr inbounds i8, ptr %st, i64 43\n  %106 = load volatile i8, ptr %105, align 1, !range !4, !noundef !2\n')
c1=runpy.run_path(D+'c1.py')['V']; x3=runpy.run_path(D+'x3.py')['V']; g=runpy.run_path(D+'e79.py'); dead=runpy.run_path(D+'dead.py')['V']; esc=runpy.run_path(D+'esc.py')['V']; j1=runpy.run_path(D+'j1.py')['V']
E79V=[g['hdr'],(g['B15'],g['ent']()),(g['A20'],g['ARM']),(g['VAL'],g['piece']('%sharing_update16','%val8'))]
V={'q_main':[Q],'q_c1a':[Q]+c1['c1a'],'q_x3h':[Q]+x3['x3h_entry_only'],'q_e79v':[Q]+E79V,'q_deadnew0':[Q]+dead['dead_vl_new0'],'q_esc_c1a':[Q]+esc['esc_c1a'],'q_j1v':[Q]+j1['j1v'],'q_e9only':[Q]+g['V']['e9only'],'q_fence':[Q]+dead['dead_fence']}
