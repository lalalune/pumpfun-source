# skip-polarity gate on 2e1379de9 post-opt IR (w14a46 sg.py with this main's names): phi holds skip, br skip, post, sweep
EDITS=[("  %_548.sroa.0.0.off0 = phi i1 [ false, %bb21 ], [ false, %bb22 ], [ false, %bb23 ], [ true, %bb19 ]\n","  %_548.sroa.0.0.off0 = phi i1 [ true, %bb21 ], [ true, %bb22 ], [ true, %bb23 ], [ false, %bb19 ]\n"),
("  br i1 %_548.sroa.0.0.off0, label %bb82, label %bb87\n","  br i1 %_548.sroa.0.0.off0, label %bb87, label %bb82\n")]
