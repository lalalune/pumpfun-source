/* 1c98*/    if (*(char *)((longlong)plVar115 + 0xd2) == '\0') {
/* 1ca8*/      iVar40 = memcmp(plVar115[0x18],&k_u32_0_1b5ba8,0x20);
/* 1ce0*/      if (iVar40 == 0) {
/* 1d20*/          goto LAB_ram_00024730;
/* 1d28*/          if (!bVar101) goto LAB_ram_00024738;
/* 1d28*/        goto LAB_ram_00024738;
/* 1ce8*/      msg = "Creator is not a system-owned wallet; fees left in the vaults";
/* 1cf8*/      len = 0x3d;
/* 1d08*/      msg = "Creator is a program; fees left in the vaults";
/* 1d18*/      len = 0x2d;
/* 1d20*/LAB_ram_00024730:
/* 1d20*/    sol_log_(msg,len);
/* 1d28*/LAB_ram_00024738:
/* 1d28*/  ppppppplVar122 = (longlong *******)0x0;
/* 1d40*/  if (!bVar37) {
/* 1d60*/    uVar5 = *(undefined1 *)(param_2 + 0x23);
/* 1d70*/    puVar48 = (undefined8 *)**(undefined8 **)(plVar115[3] + 0x58);
/* 1d88*/    ppppppplStack_2b8 = (longlong *******)puVar48[3];
/* 1d98*/    ppppppplStack_2c0 = (longlong *******)puVar48[2];
/* 1da8*/    ppppppplStack_2c8 = (longlong *******)puVar48[1];
/* 1db8*/    ppppppplStack_2d0 = (longlong *******)*puVar48;
/* 1dd0*/    iVar40 = memcmp(&ppppppplStack_2d0,NATIVE_MINT_1b5cc8,0x20);
/* 1e08*/    ppppppplStack_440 = (longlong *******)&ppppppplStack_6a0;
/* 1e28*/    uStack_450 = "creator-vault";
/* 1e30*/    uStack_438 = 0x20;
/* 1e38*/    ppppppplStack_448 = (longlong *******)0xd;
/* 1e78*/    solana_pubkey::Pubkey::find_program_address
/* 1e48*/              (&ppppppplStack_2d0,&uStack_450,2,PUMP_PROGRAM_ID_1b79df);
/* 1e88*/    ppppppplStack_500 = ppppppplStack_2b8;
/* 1e98*/    ppppppplStack_508 = ppppppplStack_2c0;
/* 1ea8*/    ppppppplStack_510 = ppppppplStack_2c8;
/* 1eb8*/    ppppppplStack_518 = ppppppplStack_2d0;
/* 1ec0*/    puVar48 = (undefined8 *)plVar115[0x21];
/* 1ec8*/    ppppppplStack_2b8 = (longlong *******)puVar48[3];
/* 1ed8*/    ppppppplStack_2c0 = (longlong *******)puVar48[2];
/* 1ee8*/    ppppppplStack_2c8 = (longlong *******)puVar48[1];
/* 1ef8*/    ppppppplStack_2d0 = (longlong *******)*puVar48;
/* 1f10*/    iVar41 = memcmp(&ppppppplStack_2d0,&ppppppplStack_518,0x20);
/* 1f40*/    plVar81 = plVar115 + 0x21;
/* 1f60*/    if (iVar41 == 0) {
