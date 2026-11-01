/* 4e58*/  solana_sysvar::clock::<impl_solana_sysvar::Sysvar_for_solana_clock::Clock>::get(&uStack_450);
/* 4e60*/  uVar121 = uStack_210;
/* 4e60*/  ppppppplVar97 = ppppppplStack_440;
/* 4e60*/  ppppppplVar46 = ppppppplStack_448;
/* 4e70*/  if ((longlong *******)uStack_450 == (longlong *******)0x0) {
/* 4e88*/    puVar48 = *(undefined8 **)*plVar115;
/* 4e98*/    ppppppplStack_2d0 = (longlong *******)*puVar48;
/* 4ea0*/    ppppppplStack_2c8 = (longlong *******)puVar48[1];
/* 4ea8*/    ppppppplStack_2c0 = (longlong *******)puVar48[2];
/* 4eb0*/    ppppppplStack_2b8 = (longlong *******)puVar48[3];
/* 4ec0*/    ppppppplStack_2b0 = (longlong *******)pppppplStack_6c0;
/* 4ef0*/    ppppppplStack_2a8 = (longlong *******)uStack_6b8;
/* 4f00*/    ppppppplStack_2a0 = (longlong *******)uStack_6b0;
/* 4f10*/    ppppppplStack_298 = (longlong *******)pppppplStack_6a8;
/* 4f40*/    puVar48 = (undefined8 *)plVar115[7];
/* 4f48*/    puVar90 = *(undefined8 **)*puVar48;
/* 4f58*/    uStack_290 = (longlong *******)*puVar90;
/* 4f68*/    ppppppplStack_288 = (longlong *******)puVar90[1];
/* 4f78*/    plStack_280 = (longlong *)puVar90[2];
/* 4f88*/    plStack_278 = (longlong *)puVar90[3];
/* 4f98*/    plStack_250 = (longlong *)puVar48[1];
/* 4fa8*/    plStack_248 = (longlong *)puVar48[2];
/* 4fb8*/    uStack_240 = puVar48[3];
/* 4fc8*/    uStack_238 = puVar48[4];
/* 4fd8*/    plStack_220 = (longlong *)puVar48[0xe];
/* 4ff0*/    ppppppplStack_230 = ppppppplStack_428;
/* 5028*/    uStack_210._4_4_ = SUB84(uVar121,4);
/* 5028*/    uStack_210._0_4_ =
/* 4f28*/         CONCAT13(uVar114,CONCAT12(bVar39 != 2,
/* 4fe8*/                                   CONCAT11(*(undefined1 *)((longlong)puVar48 + 0xa3),
/* 4fe0*/                                            *(undefined1 *)((longlong)puVar48 + 0xa5))));
/* 5040*/    uStack_270 = uStack_630;
/* 5050*/    uStack_268 = uStack_628;
/* 5060*/    uStack_260 = uStack_620;
/* 5070*/    uStack_258 = uStack_618;
/* 50a0*/    uStack_228 = uVar62;
/* 50a0*/    ppppppplStack_218 = ppppppplVar122;
/* 50a0*/    <pump_recovered::admin_cto::AdminCtoEvent_as_anchor_lang::Event>::data
/* 5080*/              (&uStack_450,&ppppppplStack_2d0);
/* 50b0*/    ppppppplStack_30 = ppppppplStack_440;
/* 50c0*/    uStack_38 = (char *)ppppppplStack_448;
/* 50d0*/    solana_program::log::sol_log_data(&uStack_38,1);
/* 50e8*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(aplStack_610,plVar115 + 0x27);
/* 5120*/    uVar114 = *(undefined1 *)(param_2 + 0x2e);
/* 5140*/    <pump_recovered::admin_cto::AdminCtoEvent_as_anchor_lang::Event>::data
/* 5090*/              (&uStack_5e0,&ppppppplStack_2d0);
/* 5170*/    puStack_5a0 = &DAT_1b64c7_1b64c7;
/* 5178*/    puStack_5a8 = &DAT_1b64bf_1b64bf;
/* 5188*/    uStack_5b8 = uStack_5e0;
/* 5198*/    lStack_5c0 = lStack_5d8;
/* 51a0*/    lStack_5c8 = lStack_5d8;
/* 51b0*/    lStack_5b0 = lStack_5d8 + lStack_5d0;
/* 51e0*/    <alloc::vec::Vec<T>_as_alloc::vec::spec_from_iter::SpecFromIter<T,I>>::from_iter
/* 51c8*/              (&ppppppplStack_470,&lStack_5c8);
/* 51e0*/    ppppppplVar46 = ppppppplStack_460;
/* 51e0*/    ppppppplVar122 = ppppppplStack_468;
/* 5208*/    ppppppplStack_30 = (longlong *******)alloc::alloc::exchange_malloc(0x22,1);
/* 5218*/    lVar50 = aplStack_610[0][3];
/* 5220*/    lVar120 = aplStack_610[0][2];
/* 5228*/    lVar103 = aplStack_610[0][1];
/* 5230*/    *ppppppplStack_30 = (longlong ******)*aplStack_610[0];
/* 5240*/    ppppppplStack_30[1] = (longlong ******)lVar103;
/* 5248*/    ppppppplStack_30[2] = (longlong ******)lVar120;
/* 5250*/    ppppppplStack_30[3] = (longlong ******)lVar50;
/* 5258*/    *(undefined2 *)(ppppppplStack_30 + 4) = 1;
/* 5268*/    uStack_38 = (char *)0x1;
/* 5270*/    ppppppplStack_28 = (longlong *******)0x1;
/* 52c0*/    solana_instruction::Instruction::new_with_bytes
/* 5280*/              (&uStack_450,PUMP_PROGRAM_ID_1b79df,ppppppplVar122,ppppppplVar46,&uStack_38);
/* 50f8*/    memcpy(&uStack_38,aplStack_610,0x30);
/* 5300*/    uStack_488 = (longlong *******)&ppppppplStack_518;
/* 5318*/    ppppppplStack_508 = (longlong *******)&ppppppplStack_4e8;
/* 5338*/    ppppppplStack_518 = (longlong *******)0x1b6807;
/* 5340*/    ppppppplStack_4e8 = (longlong *******)CONCAT71(ppppppplStack_4e8._1_7_,uVar114);
/* 5348*/    uStack_480 = 2;
/* 5350*/    ppppppplStack_500 = (longlong *******)0x1;
/* 5358*/    ppppppplStack_510 = (longlong *******)0x11;
/* 5280*/    solana_program::program::invoke_signed(alStack_598,&uStack_450,&uStack_38,1);
/* 53d0*/    if (alStack_598[0] == -0x7fffffffffffffe6) {
/* 53f0*/      lVar50 = (longlong)*ppppppplStack_30;
/* 53f8*/      *ppppppplStack_30 = (longlong ******)(lVar50 + -1);
/* 53f8*/      if (lVar50 + -1 == 0) {
/* 5418*/        ppppppplStack_30[1] = (longlong ******)((longlong)ppppppplStack_30[1] + -1);
/* 5430*/      lVar50 = (longlong)*ppppppplStack_28;
/* 5438*/      *ppppppplStack_28 = (longlong ******)(lVar50 + -1);
/* 5438*/      if (lVar50 + -1 == 0) {
/* 5450*/        ppppppplStack_28[1] = (longlong ******)((longlong)ppppppplStack_28[1] + -1);
/* 5468*/      ppppppplStack_6e0 = (longlong *******)0x2;
/* 5470*/      ppppppplStack_6c8 = ppppppplVar46;
/* 5510*/      <anchor_lang::error::Error_as_core::convert::From<solana_program_error::ProgramError>>::from
/* 54f8*/                (&ppppppplStack_890,alStack_598);
/* 5538*/      lVar50 = (longlong)*ppppppplStack_30;
/* 5540*/      *ppppppplStack_30 = (longlong ******)(lVar50 + -1);
/* 5540*/      if (lVar50 + -1 == 0) {
/* 5490*/    ppppppplStack_440 = (longlong *******)uStack_438;
/* 5498*/    ppppppplStack_448 = ppppppplVar97;
/* 54a0*/    uStack_450 = (char *)ppppppplVar46;
/* 54c8*/    <anchor_lang::error::Error_as_core::convert::From<solana_program_error::ProgramError>>::from
/* 54b0*/              (&ppppppplStack_880,&uStack_450);
/* 54d8*/    ppppppplStack_6e0 = ppppppplStack_880;
/* 54d8*/    ppppppplStack_6c8 = ppppppplStack_878;
