/* 4e18*/  uVar35 = *(undefined1 *)(puVar110[7] + 0xa5);
/* 4e30*/  solana_sysvar::clock::<impl_solana_sysvar::Sysvar_for_solana_clock::Clock>::get(&uStack_450);
/* 4e38*/  uVar42 = uStack_210;
/* 4e38*/  ppppppplVar102 = ppppppplStack_440;
/* 4e38*/  ppppppplVar83 = ppppppplStack_448;
/* 4e48*/  if ((longlong *******)uStack_450 == (longlong *******)0x0) {
/* 4e58*/    puVar45 = *(undefined8 **)*puVar110;
/* 4e68*/    ppppppplStack_2d0 = (longlong *******)*puVar45;
/* 4e70*/    ppppppplStack_2c8 = (longlong *******)puVar45[1];
/* 4e78*/    ppppppplStack_2c0 = (longlong *******)puVar45[2];
/* 4e80*/    ppppppplStack_2b8 = (longlong *******)puVar45[3];
/* 4e90*/    ppppppplStack_2b0 = (longlong *******)pppppplStack_6c0;
/* 4ec0*/    ppppppplStack_2a8 = (longlong *******)uStack_6b8;
/* 4ed0*/    ppppppplStack_2a0 = (longlong *******)uStack_6b0;
/* 4ee0*/    ppppppplStack_298 = (longlong *******)pppppplStack_6a8;
/* 4f10*/    puVar45 = (undefined8 *)puVar110[7];
/* 4f18*/    puVar91 = *(undefined8 **)*puVar45;
/* 4f28*/    uStack_290 = (longlong *******)*puVar91;
/* 4f38*/    ppppppplStack_288 = (longlong *******)puVar91[1];
/* 4f48*/    plStack_280 = (longlong *)puVar91[2];
/* 4f58*/    plStack_278 = (longlong *)puVar91[3];
/* 4f68*/    plStack_250 = (longlong *)puVar45[1];
/* 4f78*/    plStack_248 = (longlong *)puVar45[2];
/* 4f88*/    uStack_240 = puVar45[3];
/* 4f98*/    uStack_238 = puVar45[4];
/* 4fb0*/    ppppppplStack_230 = ppppppplStack_428;
/* 4fe8*/    uStack_210._4_4_ = SUB84(uVar42,4);
/* 4fe8*/    uStack_210._0_4_ =
/* 4f00*/         CONCAT13(uVar98,CONCAT12(cVar1 != '\x02',
/* 4fa8*/                                  CONCAT11(*(undefined1 *)((longlong)puVar45 + 0xa3),uVar35)));
/* 5008*/    lStack_270 = uStack_630;
/* 5018*/    lStack_268 = uStack_628;
/* 5028*/    uStack_260 = uStack_620;
/* 5038*/    uStack_258 = uStack_618;
/* 5068*/    uStack_228 = uVar59;
/* 5068*/    plStack_220 = (longlong *)uVar120;
/* 5068*/    ppppppplStack_218 = ppppppplVar69;
/* 5068*/    <pump_recovered::admin_cto::AdminCtoEvent_as_anchor_lang::Event>::data
/* 5048*/              (&uStack_450,&ppppppplStack_2d0);
/* 5078*/    ppppppplStack_30 = ppppppplStack_440;
/* 5088*/    uStack_38 = (char *)ppppppplStack_448;
/* 5098*/    solana_program::log::sol_log_data(&uStack_38,1);
/* 50b0*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(aplStack_610,puVar110 + 0x27);
/* 50e8*/    uVar98 = *(undefined1 *)(param_2 + 0x2e);
/* 5110*/    <pump_recovered::admin_cto::AdminCtoEvent_as_anchor_lang::Event>::data
/* 5058*/              (&uStack_5e0,&ppppppplStack_2d0);
/* 5140*/    puStack_5a0 = &DAT_1b64c7_1b64c7;
/* 5148*/    puStack_5a8 = &DAT_1b64bf_1b64bf;
/* 5158*/    uStack_5b8 = uStack_5e0;
/* 5168*/    lStack_5c0 = lStack_5d8;
/* 5170*/    lStack_5c8 = lStack_5d8;
/* 5180*/    lStack_5b0 = lStack_5d8 + lStack_5d0;
/* 51b0*/    <alloc::vec::Vec<T>_as_alloc::vec::spec_from_iter::SpecFromIter<T,I>>::from_iter
/* 5198*/              (&ppppppplStack_470,&lStack_5c8);
/* 51b0*/    ppppppplVar83 = ppppppplStack_460;
/* 51b0*/    ppppppplVar69 = ppppppplStack_468;
/* 51d8*/    ppppppplStack_30 = (longlong *******)alloc::alloc::exchange_malloc(0x22,1);
/* 51e8*/    lVar47 = aplStack_610[0][3];
/* 51f0*/    lVar106 = aplStack_610[0][2];
/* 51f8*/    lVar48 = aplStack_610[0][1];
/* 5200*/    *ppppppplStack_30 = (longlong ******)*aplStack_610[0];
/* 5210*/    ppppppplStack_30[1] = (longlong ******)lVar48;
/* 5218*/    ppppppplStack_30[2] = (longlong ******)lVar106;
/* 5220*/    ppppppplStack_30[3] = (longlong ******)lVar47;
/* 5228*/    *(undefined2 *)(ppppppplStack_30 + 4) = 1;
/* 5238*/    uStack_38 = (char *)0x1;
/* 5240*/    pppppplStack_28 = (longlong ******)0x1;
/* 5290*/    solana_instruction::Instruction::new_with_bytes
/* 5250*/              (&uStack_450,PUMP_PROGRAM_ID_1b79df,ppppppplVar69,ppppppplVar83,&uStack_38);
/* 50c0*/    memcpy(&uStack_38,aplStack_610,0x30);
/* 52d0*/    uStack_488 = (longlong *******)&ppppppplStack_518;
/* 52e8*/    ppppppplStack_508 = (longlong *******)&ppppppplStack_4e8;
/* 5308*/    ppppppplStack_518 = (longlong *******)0x1b6807;
/* 5318*/    ppppppplStack_4e8 = (longlong *******)CONCAT71(ppppppplStack_4e8._1_7_,uVar98);
/* 5320*/    uStack_480 = 2;
/* 5328*/    pppppplStack_500 = (longlong ******)0x1;
/* 5330*/    ppppppplStack_510 = (longlong *******)0x11;
/* 5250*/    solana_program::program::invoke_signed(alStack_598,&uStack_450,&uStack_38,1);
/* 53a8*/    if (alStack_598[0] == -0x7fffffffffffffe6) {
/* 53c8*/      lVar47 = (longlong)*ppppppplStack_30;
/* 53d0*/      *ppppppplStack_30 = (longlong ******)(lVar47 + -1);
/* 53d0*/      if (lVar47 + -1 == 0) {
/* 53f0*/        ppppppplStack_30[1] = (longlong ******)((longlong)ppppppplStack_30[1] + -1);
/* 5408*/      lVar47 = (longlong)*pppppplStack_28;
/* 5410*/      *pppppplStack_28 = (longlong *****)(lVar47 + -1);
/* 5410*/      if (lVar47 + -1 == 0) {
/* 5428*/        pppppplStack_28[1] = (longlong *****)((longlong)pppppplStack_28[1] + -1);
/* 5440*/      ppppppplStack_6f0 = (longlong *******)0x2;
/* 52a0*/      ppppppplStack_6e8 = (longlong *******)&uStack_38;
/* 54e0*/      <anchor_lang::error::Error_as_core::convert::From<solana_program_error::ProgramError>>::from
/* 54c8*/                (&ppppppplStack_890,alStack_598);
/* 5508*/      lVar47 = (longlong)*ppppppplStack_30;
/* 5510*/      *ppppppplStack_30 = (longlong ******)(lVar47 + -1);
/* 5510*/      if (lVar47 + -1 == 0) {
/* 5468*/    ppppppplStack_440 = (longlong *******)uStack_438;
/* 5470*/    ppppppplStack_448 = ppppppplVar102;
/* 5478*/    uStack_450 = (char *)ppppppplVar83;
/* 54a0*/    <anchor_lang::error::Error_as_core::convert::From<solana_program_error::ProgramError>>::from
/* 5488*/              (&ppppppplStack_880,&uStack_450);
/* 54b8*/    ppppppplStack_6f0 = ppppppplStack_880;
/* 54b8*/    ppppppplStack_6e8 = ppppppplStack_878;
