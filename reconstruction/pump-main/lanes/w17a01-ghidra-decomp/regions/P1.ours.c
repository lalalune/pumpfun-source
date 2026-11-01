/* 4a68*/  lVar106 = puVar110[7];
/* 4a70*/  uStack_618 = *(undefined8 *)(lVar106 + 0x20);
/* 4a80*/  uStack_620 = *(undefined8 *)(lVar106 + 0x18);
/* 4a90*/  uStack_628 = *(undefined8 *)(lVar106 + 0x10);
/* 4aa0*/  uStack_630 = *(undefined8 *)(lVar106 + 8);
/* 4ab0*/  *(ulonglong *)(lVar106 + 8) = CONCAT44(uStack_57c,uStack_580);
/* 4ac0*/  *(ulonglong *)(lVar106 + 0x10) = CONCAT17(uStack_571,uStack_578);
/* 4ad0*/  *(ulonglong *)(lVar106 + 0x18) = CONCAT17(uStack_569,uStack_570);
/* 4ae0*/  *(ulonglong *)(lVar106 + 0x20) = CONCAT17(uStack_561,uStack_568);
/* 4af0*/  uVar59 = *(undefined8 *)(lVar106 + 0x70);
/* 4b08*/  *(byte *)(puVar110[7] + 0xa5) = param_3 & 1;
/* 4b38*/  if (param_4 == 1) {
/* 4b48*/    *(longlong *)(puVar110[7] + 0x70) = lVar47;
/* 4b60*/  *(undefined1 *)(puVar110[7] + 0xa4) = 0;
/* 4b70*/  uVar120 = *(undefined8 *)(puVar110[7] + 0x70);
/* 4b80*/  lVar47 = solana_account_info::AccountInfo::data_is_empty(puVar110[0xe]);
/* 4b90*/  if ((lVar47 == 0) &&
/* 4b98*/     (iVar39 = memcmp(*(undefined8 *)(puVar110[0xe] + 0x18),PUMP_AMM_PROGRAM_ID_1b79ff,0x20),
/* 4bd8*/     iVar39 == 0)) {
/* 4c10*/    uVar98 = *(undefined1 *)(puVar110[7] + 0xa5);
/* 4c38*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 4c20*/              (&ppppppplStack_2b8,puVar110[0xb]);
/* 4c40*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(&uStack_450,*puVar110);
/* 4c80*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 4c68*/              (&ppppppplStack_420,puVar110[0xc]);
/* 4c88*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_3f0,puVar110[0xe]);
/* 4ca8*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_3c0,puVar110[0xd]);
/* 4cc8*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_390,puVar110[6]);
/* 4ce8*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_360,puVar110[0xf]);
/* 4d08*/    <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_330,puVar110[0xb]);
/* 4c50*/    memcpy(&ppppppplStack_288,&uStack_450,0x150);
/* 4d58*/    ppuStack_138 = &puStack_4d0;
/* 4d68*/    plStack_130 = (longlong *)0x1;
/* 4d70*/    ppppppplStack_2c0 = (longlong *******)0x0;
/* 4d78*/    ppppppplStack_2c8 = (longlong *******)0x8;
/* 4d80*/    ppppppplStack_2d0 = (longlong *******)0x0;
/* 4de8*/    pump_recovered::pump_amm::cpi::admin_cto_pool
/* 4db0*/              (&ppppppplStack_870,&ppppppplStack_2d0,&uStack_580,uVar98);
/* 4df0*/    uVar98 = 1;
/* 4e08*/    ppppppplStack_6f0 = ppppppplStack_870;
/* 4e08*/    ppppppplStack_6e8 = ppppppplStack_868;
/* 4e08*/    if (ppppppplStack_870 != (longlong *******)0x2) goto LAB_ram_00028248;
/* 4bf8*/    sol_log_("No canonical pump pool for this mint; curve only",0x30);
/* 4c00*/    uVar98 = 0;
