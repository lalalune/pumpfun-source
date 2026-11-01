/* 1c98*/    if (*(char *)((longlong)puVar110 + 0xd2) == '\0') {
/* 1ca8*/      iVar39 = memcmp(puVar110[0x18],&k_u32_0_1b5ba8,0x20);
/* 1ce0*/      if (iVar39 == 0) {
/* 1d20*/          goto LAB_ram_00024730;
/* 1ce8*/      pcVar46 = "Creator is not a system-owned wallet; fees left in the vaults";
/* 1cf8*/      uVar99 = 0x3d;
/* 1d08*/      pcVar46 = "Creator is a program; fees left in the vaults";
/* 1d18*/      uVar99 = 0x2d;
/* 1d20*/LAB_ram_00024730:
/* 1d20*/    sol_log_(pcVar46,uVar99);
/* 1d48*/    uVar98 = *(undefined1 *)(param_2 + 0x23);
/* 1d58*/    puVar45 = (undefined8 *)**(undefined8 **)(puVar110[3] + 0x58);
/* 1d70*/    ppppppplStack_2b8 = (longlong *******)puVar45[3];
/* 1d80*/    ppppppplStack_2c0 = (longlong *******)puVar45[2];
/* 1d90*/    ppppppplStack_2c8 = (longlong *******)puVar45[1];
/* 1da0*/    ppppppplStack_2d0 = (longlong *******)*puVar45;
/* 1db8*/    iVar39 = memcmp(&ppppppplStack_2d0,NATIVE_MINT_1b5cc8,0x20);
/* 1df0*/    ppppppplStack_440 = (longlong *******)&uStack_6a0;
/* 1e10*/    uStack_450 = "creator-vault";
/* 1e18*/    uStack_438 = 0x20;
/* 1e20*/    ppppppplStack_448 = (longlong *******)0xd;
/* 1e60*/    solana_pubkey::Pubkey::find_program_address
/* 1e30*/              (&ppppppplStack_2d0,&uStack_450,2,PUMP_PROGRAM_ID_1b79df);
/* 1e70*/    pppppplStack_500 = (longlong ******)ppppppplStack_2b8;
/* 1e80*/    ppppppplStack_508 = ppppppplStack_2c0;
/* 1e90*/    ppppppplStack_510 = ppppppplStack_2c8;
/* 1ea0*/    ppppppplStack_518 = ppppppplStack_2d0;
/* 1ea8*/    puVar45 = (undefined8 *)puVar110[0x21];
/* 1eb0*/    ppppppplStack_2b8 = (longlong *******)puVar45[3];
/* 1ec0*/    ppppppplStack_2c0 = (longlong *******)puVar45[2];
/* 1ed0*/    ppppppplStack_2c8 = (longlong *******)puVar45[1];
/* 1ee0*/    ppppppplStack_2d0 = (longlong *******)*puVar45;
/* 1ef8*/    iVar40 = memcmp(&ppppppplStack_2d0,&ppppppplStack_518,0x20);
/* 1f28*/    puVar45 = puVar110 + 0x21;
/* 1f40*/    if (iVar40 == 0) {
