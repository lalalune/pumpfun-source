/* 4ac0*/  lVar120 = plVar115[7];
/* 4ac8*/  uStack_618 = *(undefined8 *)(lVar120 + 0x20);
/* 4ad8*/  uStack_620 = *(undefined8 *)(lVar120 + 0x18);
/* 4ae8*/  uStack_628 = *(undefined8 *)(lVar120 + 0x10);
/* 4af8*/  uStack_630 = *(undefined8 *)(lVar120 + 8);
/* 4b10*/  *(longlong ********)(lVar120 + 8) = ppppppplStack_580;
/* 4b20*/  *(longlong ********)(lVar120 + 0x10) = ppppppplStack_578;
/* 4b30*/  *(longlong ********)(lVar120 + 0x18) = ppppppplStack_570;
/* 4b40*/  *(longlong ********)(lVar120 + 0x20) = ppppppplStack_568;
/* 4b48*/  uVar62 = *(undefined8 *)(lVar120 + 0x70);
/* 4b58*/  *(undefined1 *)(plVar115[7] + 0xa5) = uVar114;
/* 4b70*/  *(bool *)(plVar115[7] + 0xa3) = bVar92;
/* 4b88*/  if (bVar38) {
/* 4b98*/    *(longlong *)(plVar115[7] + 0x70) = lVar50;
/* 4bb0*/  *(undefined1 *)(plVar115[7] + 0xa4) = 0;
/* 4bc0*/  lVar50 = plVar115[0xe];
/* 4bc8*/  iVar40 = memcmp(*(undefined8 *)(lVar50 + 0x18),PUMP_AMM_PROGRAM_ID_1b79ff,0x20);
/* 4c00*/  if ((iVar40 == 0) &&
/* 4c10*/     (lVar50 = solana_account_info::AccountInfo::data_is_empty(lVar50), lVar50 == 0)) {
/* 4c70*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 4c58*/              (&ppppppplStack_2b8,plVar115[0xb]);
/* 4c78*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(&uStack_450,*plVar115);
/* 4cb8*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 4ca0*/              (&ppppppplStack_420,plVar115[0xc]);
/* 4cc0*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_3f0,plVar115[0xe]);
/* 4ce0*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_3c0,plVar115[0xd]);
/* 4d00*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_390,plVar115[6]);
/* 4d20*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_360,plVar115[0xf]);
/* 4d40*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_330,plVar115[0xb]);
/* 4c88*/    memcpy(&ppppppplStack_288,&uStack_450,0x150);
/* 4d98*/    pppppplStack_138 = (longlong ******)&pppppplStack_4d0;
/* 4da8*/    plStack_130 = (longlong *)0x1;
/* 4db0*/    ppppppplStack_2c0 = (longlong *******)0x0;
/* 4db8*/    ppppppplStack_2c8 = (longlong *******)0x8;
/* 4dc0*/    ppppppplStack_2d0 = (longlong *******)0x0;
/* 4e28*/    pump_recovered::pump_amm::cpi::admin_cto_pool
/* 4df0*/              (&ppppppplStack_870,&ppppppplStack_2d0,&ppppppplStack_580,uVar114);
/* 4e30*/    uVar114 = 1;
/* 4e48*/    ppppppplStack_6e0 = ppppppplStack_870;
/* 4e48*/    ppppppplStack_6c8 = ppppppplStack_868;
/* 4e48*/    if (ppppppplStack_870 != (longlong *******)0x2) goto LAB_ram_00028280;
/* 4c38*/    sol_log_("No canonical pump pool for this mint; curve only",0x30);
/* 4c40*/    uVar114 = 0;
