              
              void pump_recovered::set_creator::set(undefined8 *param_1,longlong param_2,undefined8 *param_3)
              
              {
                undefined1 uVar1;
                undefined1 uVar2;
                undefined1 uVar3;
                undefined1 uVar4;
                int iVar5;
                longlong *plVar6;
                undefined8 *puVar7;
                longlong lVar8;
                undefined8 *puVar9;
                undefined8 uVar10;
                undefined8 uVar11;
                undefined8 *puVar12;
                char *pcVar13;
                undefined8 uVar14;
                undefined8 uVar15;
                longlong *plVar16;
                undefined8 uVar17;
                longlong lVar18;
                undefined8 *puVar19;
                undefined8 uStack_208;
                char *pcStack_200;
                undefined8 uStack_1f8;
                char *pcStack_1f0;
                undefined8 uStack_1e8;
                char *pcStack_1e0;
                undefined8 uStack_1d8;
                char *pcStack_1d0;
                undefined8 uStack_1c8;
                undefined8 uStack_1c0;
                undefined8 uStack_1b8;
                undefined8 uStack_1b0;
                undefined8 uStack_1a8;
                undefined8 uStack_1a0;
                undefined8 uStack_198;
                undefined8 uStack_190;
                undefined8 uStack_188;
                undefined8 uStack_180;
                undefined8 uStack_178;
                undefined8 uStack_170;
                undefined8 *puStack_168;
                undefined8 *puStack_160;
                undefined8 uStack_158;
                undefined8 uStack_150;
                undefined8 uStack_140;
                undefined8 uStack_128;
                undefined8 uStack_120;
                undefined8 uStack_118;
                undefined8 uStack_110;
                undefined8 *puStack_e8;
                longlong *plStack_e0;
                longlong *plStack_d8;
                undefined8 uStack_d0;
                undefined8 uStack_c8;
                undefined1 uStack_c0;
                undefined1 uStack_bf;
                undefined1 uStack_be;
                undefined5 uStack_bd;
                longlong alStack_98 [3];
                char *pcStack_80;
                longlong *plStack_78;
                char ****ppppcStack_70;
                undefined8 uStack_68;
                undefined8 uStack_60;
                undefined1 uStack_58;
                undefined1 uStack_57;
                undefined1 uStack_56;
                char ***pppcStack_50;
                undefined8 uStack_48;
                char **ppcStack_40;
                undefined8 uStack_38;
                undefined1 *puStack_30;
                undefined8 uStack_28;
                undefined1 uStack_19;
                longlong alStack_18 [3];
                
/*   18-   18*/  lVar18 = *(longlong *)(param_2 + 8);
/*   20-   20*/  uStack_150 = 0;
/*   28-   28*/  uStack_158 = 0;
/*   30-   30*/  puStack_160 = (undefined8 *)0x0;
/*   38-   38*/  puStack_168 = (undefined8 *)0x0;
/*   48-   48*/  puVar19 = (undefined8 *)(lVar18 + 0x1e8);
/*   58-   70*/  iVar5 = memcmp(puVar19,&puStack_168,0x20);
/*   88-   88*/  if (iVar5 != 0) {
/*  230-  230*/    pcVar13 = "Bonding curve has creator already set";
/*  248-  248*/    sol_log_("Bonding curve has creator already set",0x25);
/*  250-  250*/    uStack_1d8 = 2;
/*  260-  260*/    goto LAB_ram_00039220;
                }
/*   90-   98*/  puVar7 = (undefined8 *)**(longlong **)(lVar18 + 0x178);
/*   a0-   a0*/  uStack_1b0 = puVar7[3];
/*   b0-   b0*/  uStack_1b8 = puVar7[2];
/*   c0-   c0*/  uStack_1c0 = puVar7[1];
/*   d0-   d0*/  uStack_1c8 = *puVar7;
/*   e0-   e8*/  puVar7 = (undefined8 *)**(longlong **)(lVar18 + 0x1e0);
/*   f0-   f0*/  uStack_190 = puVar7[3];
/*  100-  100*/  uStack_198 = puVar7[2];
/*  110-  110*/  uStack_1a0 = puVar7[1];
/*  120-  120*/  uStack_1a8 = *puVar7;
/*  130-  148*/  if (*(longlong *)(lVar18 + 0x48) == -0x8000000000000000) {
/*  158-  160*/    *(undefined8 *)(lVar18 + 0x200) = param_3[3];
/*  168-  170*/    *(undefined8 *)(lVar18 + 0x1f8) = param_3[2];
/*  178-  180*/    *(undefined8 *)(lVar18 + 0x1f0) = param_3[1];
/*  188-  190*/    *puVar19 = *param_3;
/*  1a0-  1a8*/    solana_sysvar::clock::<impl_solana_sysvar::Sysvar_for_solana_clock::Clock>::get(&puStack_168);
/*  1a8-  1a8*/    uVar10 = uStack_158;
/*  1a8-  1a8*/    puVar19 = puStack_160;
/*  1b8-  1b8*/    if (puStack_168 != (undefined8 *)0x0) {
/*  1d8-  1d8*/      uStack_158 = uStack_150;
/*  1e0-  1e0*/      puStack_160 = (undefined8 *)uVar10;
/*  1e8-  1e8*/      puStack_168 = puVar19;
/*  210-  210*/      <anchor_lang::error::Error_as_core::convert::From<solana_program_error::ProgramError>>::from
/*  1f8-  210*/                (&uStack_1f8,&puStack_168);
/*  228-  228*/      pcVar13 = pcStack_1f0;
/*  228-  228*/      uStack_1d8 = uStack_1f8;
/*  260-  260*/      goto LAB_ram_00039220;
                  }
/*  3f8-  408*/    puVar19 = (undefined8 *)0x0;
/*  3f0-  408*/    if (puRam0000000300000000 + -0x20 <= puRam0000000300000000) {
/*  3f0-  420*/      puVar19 = puRam0000000300000000 + -0x20;
                  }
/*  428-  438*/    puVar7 = (undefined8 *)0x300007f00;
/*  438-  438*/    if (puRam0000000300000000 != (undefined8 *)0x0) {
/*  440-  440*/      puVar7 = puVar19;
                  }
/*  458-  460*/    if (puVar7 < (undefined8 *)0x300000008) goto LAB_ram_00039420;
/*  4a0-  4a0*/    puRam0000000300000000 = puVar7;
/*  4a0-  4a0*/    puVar7[1] = uStack_140;
/*  4b8-  4b8*/    *puVar7 = 0xd248fbf5257b34ed;
/*  4c8-  4c8*/    puVar7[5] = uStack_1b0;
/*  4d8-  4d8*/    puVar7[4] = uStack_1b8;
/*  4e8-  4e8*/    puVar7[3] = uStack_1c0;
/*  4f8-  4f8*/    puVar7[2] = uStack_1c8;
/*  508-  508*/    puVar7[6] = uStack_1a8;
/*  518-  518*/    puVar7[7] = uStack_1a0;
/*  528-  528*/    puVar7[8] = uStack_198;
/*  538-  538*/    puVar7[9] = uStack_190;
/*  540-  548*/    puVar7[10] = *param_3;
/*  550-  558*/    puVar7[0xb] = param_3[1];
/*  560-  568*/    puVar7[0xc] = param_3[2];
/*  570-  578*/    puVar7[0xd] = param_3[3];
/*  588-  588*/    puStack_160 = (undefined8 *)0x70;
/*  5b0-  5b0*/    puStack_168 = puVar7;
/*  598-  5b0*/    solana_program::log::sol_log_data(&puStack_168,1);
/*  5b8-  5b8*/    plVar16 = *(longlong **)(lVar18 + 0x188);
/*  5c0-  5c0*/    lVar8 = *plVar16;
/*  5e0-  5e0*/    puVar19 = *(undefined8 **)(lVar18 + 0x180);
/*  5c8-  5e8*/    *plVar16 = lVar8 + 1;
/*  5c8-  5f8*/    if (lVar8 + 1 == 0) goto LAB_ram_000395b8;
/*  600-  600*/    plVar6 = *(longlong **)(lVar18 + 400);
/*  608-  608*/    lVar8 = *plVar6;
/*  610-  638*/    *plVar6 = lVar8 + 1;
/*  5f8-  640*/    if (lVar8 + 1 == 0) goto LAB_ram_000395b8;
/*  678-  688*/    puVar7 = (undefined8 *)0x0;
/*  670-  688*/    if (puRam0000000300000000 + -0x20 <= puRam0000000300000000) {
/*  670-  6a0*/      puVar7 = puRam0000000300000000 + -0x20;
                  }
/*  6b0-  6c0*/    puVar9 = (undefined8 *)0x300007f00;
/*  6c0-  6c0*/    if (puRam0000000300000000 != (undefined8 *)0x0) {
/*  6c8-  6c8*/      puVar9 = puVar7;
                  }
/*  460-  6e8*/    if (puVar9 < (undefined8 *)0x300000008) goto LAB_ram_00039420;
/*  6f8-  6f8*/    uVar1 = *(undefined1 *)(param_2 + 0x23);
/*  700-  700*/    uVar2 = *(undefined1 *)(lVar18 + 0x1aa);
/*  710-  710*/    uVar3 = *(undefined1 *)(lVar18 + 0x1a9);
/*  720-  720*/    uVar4 = *(undefined1 *)(lVar18 + 0x1a8);
/*  730-  730*/    uVar10 = *(undefined8 *)(lVar18 + 0x1a0);
/*  740-  740*/    uVar11 = *(undefined8 *)(lVar18 + 0x198);
/*  768-  768*/    puRam0000000300000000 = puVar9;
/*  768-  768*/    puVar9[1] = uStack_140;
/*  780-  780*/    *puVar9 = 0xd248fbf5257b34ed;
/*  790-  790*/    puVar9[5] = uStack_1b0;
/*  7a0-  7a0*/    puVar9[4] = uStack_1b8;
/*  7b0-  7b0*/    puVar9[3] = uStack_1c0;
/*  7c0-  7c0*/    puVar9[2] = uStack_1c8;
/*  7d0-  7d0*/    puVar9[6] = uStack_1a8;
/*  7e0-  7e0*/    puVar9[7] = uStack_1a0;
/*  7f0-  7f0*/    puVar9[8] = uStack_198;
/*  800-  800*/    puVar9[9] = uStack_190;
/*  808-  810*/    puVar9[10] = *param_3;
/*  818-  820*/    puVar9[0xb] = param_3[1];
/*  828-  830*/    puVar9[0xc] = param_3[2];
/*  838-  840*/    puVar9[0xd] = param_3[3];
/*  868-  878*/    puVar7 = (undefined8 *)0x300008000;
/*  878-  878*/    if (puRam0000000300000000 != (undefined8 *)0x0) {
/*  880-  880*/      puVar7 = puRam0000000300000000;
                  }
/*  898-  8b0*/    puVar12 = (undefined8 *)0x0;
/*  890-  8b0*/    if (puVar7 + -0xf <= puVar7) {
/*  890-  8c8*/      puVar12 = puVar7 + -0xf;
                  }
/*  8e0-  8e0*/    if (puVar12 < (undefined8 *)0x300000008) {
/* 17e0- 17e0*/                    /* WARNING: Subroutine does not return */
/* 17e0- 17e0*/      alloc::raw_vec::handle_error(1,0x78);
                  }
/*  910-  910*/    puRam0000000300000000 = puVar12;
/*  910-  910*/    *puVar12 = 0x1d9acb512ea545e4;
/*  918-  918*/    lVar18 = 0;
                  do {
/*  938-  948*/      *(undefined1 *)((longlong)puVar12 + lVar18 + 8) = *(undefined1 *)((longlong)puVar9 + lVar18);
/*  950-  950*/      lVar18 = lVar18 + 1;
/*  958-  958*/    } while (lVar18 != 0x70);
/*  990-  9a0*/    puVar7 = (undefined8 *)0x0;
/*  988-  9a0*/    if ((undefined8 *)((longlong)puRam0000000300000000 + -0x22) <= puRam0000000300000000) {
/*  988-  9b8*/      puVar7 = (undefined8 *)((longlong)puRam0000000300000000 + -0x22);
                  }
/*  9c0-  9d0*/    puVar9 = (undefined8 *)0x300007fde;
/*  9d0-  9d0*/    if (puRam0000000300000000 != (undefined8 *)0x0) {
/*  9d8-  9d8*/      puVar9 = puVar7;
                  }
/*  9f8-  a00*/    if (puVar9 < (undefined8 *)0x300000008) goto LAB_ram_000399c0;
/*  a38-  a38*/    uVar14 = *puVar19;
/*  a40-  a40*/    uVar15 = puVar19[1];
/*  a48-  a48*/    uVar17 = puVar19[2];
/*  a58-  a58*/    puRam0000000300000000 = puVar9;
/*  a50-  a58*/    puVar9[3] = puVar19[3];
/*  a60-  a60*/    puVar9[2] = uVar17;
/*  a68-  a68*/    puVar9[1] = uVar15;
/*  a70-  a70*/    *puVar9 = uVar14;
/*  a78-  a78*/    *(undefined2 *)(puVar9 + 4) = 1;
/*  a88-  a88*/    plStack_d8 = (longlong *)0x1;
/*  a90-  a90*/    puStack_e8 = (undefined8 *)0x1;
/*  ad8-  ad8*/    plStack_e0 = puVar9;
/*  ad8-  ad8*/    solana_instruction::Instruction::new_with_bytes
/*  aa0-  ad8*/              (&puStack_168,PUMP_PROGRAM_ID_1b79df,puVar12,0x78,&puStack_e8);
/*  b58-  b58*/    ppcStack_40 = &pcStack_80;
/*  b70-  b70*/    ppppcStack_70 = &pppcStack_50;
/*  b90-  b90*/    pcStack_80 = "__event_authority";
/*  b98-  b98*/    pppcStack_50 = (char ***)CONCAT71(pppcStack_50._1_7_,uVar1);
/*  ba0-  ba0*/    uStack_38 = 2;
/*  ba8-  ba8*/    uStack_68 = 1;
/*  bb0-  bb0*/    plStack_78 = (longlong *)0x11;
/*  c10-  c10*/    puStack_e8 = puVar19;
/*  c10-  c10*/    plStack_e0 = plVar16;
/*  c10-  c10*/    plStack_d8 = plVar6;
/*  c10-  c10*/    uStack_d0 = uVar11;
/*  c10-  c10*/    uStack_c8 = uVar10;
/*  c10-  c10*/    uStack_c0 = uVar4;
/*  c10-  c10*/    uStack_bf = uVar3;
/*  c10-  c10*/    uStack_be = uVar2;
/*  aa0-  c10*/    solana_program::program::invoke_signed(alStack_18,&puStack_168,&puStack_e8,1);
/*  c30-  c30*/    if (alStack_18[0] == -0x7fffffffffffffe6) {
/*  c40-  c40*/      lVar18 = *plVar16;
/*  c48-  c50*/      *plVar16 = lVar18 + -1;
/*  c48-  c58*/      if (lVar18 + -1 == 0) {
/*  c60-  c70*/        plVar16[1] = plVar16[1] + -1;
                    }
/*  c80-  c88*/      pcVar13 = (char *)(*plVar6 + -1);
/*  c90-  c90*/      *plVar6 = (longlong)pcVar13;
/*  ca0-  ca0*/      goto joined_r0x00039c60;
                  }
/* 1690- 1690*/    <anchor_lang::error::Error_as_core::convert::From<solana_program_error::ProgramError>>::from
/* 1678- 1690*/              (&uStack_208,alStack_18);
/* 16b8- 16b8*/    lVar18 = *plStack_e0;
/* 16c0- 16c8*/    *plStack_e0 = lVar18 + -1;
/* 16c0- 16d0*/    if (lVar18 + -1 == 0) {
/* 16d8- 16e8*/      plStack_e0[1] = plStack_e0[1] + -1;
                  }
/* 16f0- 16f8*/    lVar18 = *plStack_d8 + -1;
/* 1700- 1700*/    *plStack_d8 = lVar18;
/* 1708- 1708*/    uStack_1d8 = uStack_208;
/* 1708- 1708*/    pcVar13 = pcStack_200;
                }
                else {
/*  278-  280*/    if (*(longlong *)(lVar18 + 0x58) == 0) {
/*  2a8-  2a8*/                    /* WARNING: Subroutine does not return */
/*  2a8-  2a8*/      core::panicking::panic_bounds_check(0,0,&obj_1bdb18_1bdb18);
                  }
/*  2b0-  2b0*/    lVar8 = *(longlong *)(lVar18 + 0x50);
/*  2b8-  2b8*/    uStack_170 = *(undefined8 *)(lVar8 + 0x19);
/*  2c8-  2c8*/    uStack_178 = *(undefined8 *)(lVar8 + 0x11);
/*  2d8-  2d8*/    uStack_180 = *(undefined8 *)(lVar8 + 9);
/*  2e8-  2e8*/    uStack_188 = *(undefined8 *)(lVar8 + 1);
/*  2f8-  2f8*/    uVar10 = *(undefined8 *)(lVar8 + 1);
/*  300-  300*/    uVar11 = *(undefined8 *)(lVar8 + 9);
/*  308-  308*/    uVar14 = *(undefined8 *)(lVar8 + 0x11);
/*  310-  318*/    *(undefined8 *)(lVar18 + 0x200) = *(undefined8 *)(lVar8 + 0x19);
/*  320-  320*/    *(undefined8 *)(lVar18 + 0x1f8) = uVar14;
/*  328-  328*/    *(undefined8 *)(lVar18 + 0x1f0) = uVar11;
/*  330-  330*/    *puVar19 = uVar10;
/*  340-  348*/    solana_sysvar::clock::<impl_solana_sysvar::Sysvar_for_solana_clock::Clock>::get(&puStack_e8);
/*  348-  348*/    plVar6 = plStack_d8;
/*  348-  348*/    plVar16 = plStack_e0;
/*  358-  358*/    if (puStack_e8 != (undefined8 *)0x0) {
/*  378-  378*/      plStack_d8 = (longlong *)uStack_d0;
/*  380-  380*/      plStack_e0 = plVar6;
/*  388-  388*/      puStack_e8 = plVar16;
/*  3b0-  3b0*/      <anchor_lang::error::Error_as_core::convert::From<solana_program_error::ProgramError>>::from
/*  398-  3b0*/                (&uStack_1d8,&puStack_e8);
/*  3c8-  3c8*/      pcVar13 = pcStack_1d0;
/*  260-  260*/      goto LAB_ram_00039220;
                  }
/*  cd0-  cd0*/    uVar10 = CONCAT53(uStack_bd,CONCAT12(uStack_be,CONCAT11(uStack_bf,uStack_c0)));
/*  cd8-  ce0*/    puVar19 = (undefined8 *)**(longlong **)(lVar18 + 0x118);
/*  ce8-  ce8*/    uStack_110 = puVar19[3];
/*  cf8-  cf8*/    uStack_118 = puVar19[2];
/*  d08-  d08*/    uStack_120 = puVar19[1];
/*  d18-  d18*/    uStack_128 = *puVar19;
/*  d40-  d60*/    puVar19 = (undefined8 *)0x0;
/*  d58-  d60*/    if (puRam0000000300000000 + -0x20 <= puRam0000000300000000) {
/*  d58-  d78*/      puVar19 = puRam0000000300000000 + -0x20;
                  }
/*  d80-  d90*/    puVar7 = (undefined8 *)0x300007f00;
/*  d90-  d90*/    if (puRam0000000300000000 != (undefined8 *)0x0) {
/*  d98-  d98*/      puVar7 = puVar19;
                  }
/*  db0-  db0*/    if (puVar7 < (undefined8 *)0x300000008) {
/*  460-  460*/LAB_ram_00039420:
/*  470-  470*/                    /* WARNING: Subroutine does not return */
/*  470-  470*/      alloc::raw_vec::handle_error(1,0x100);
                  }
/*  df0-  df0*/    puRam0000000300000000 = puVar7;
/*  df0-  df0*/    puVar7[1] = uVar10;
/*  e08-  e08*/    *puVar7 = 0xa2bf697f2006cb8e;
/*  e18-  e18*/    puVar7[5] = uStack_1b0;
/*  e28-  e28*/    puVar7[4] = uStack_1b8;
/*  e38-  e38*/    puVar7[3] = uStack_1c0;
/*  e48-  e48*/    puVar7[2] = uStack_1c8;
/*  e58-  e58*/    puVar7[9] = uStack_190;
/*  e68-  e68*/    puVar7[8] = uStack_198;
/*  e78-  e78*/    puVar7[7] = uStack_1a0;
/*  e88-  e88*/    puVar7[6] = uStack_1a8;
/*  e98-  e98*/    puVar7[0xd] = uStack_110;
/*  ea8-  ea8*/    puVar7[0xc] = uStack_118;
/*  eb8-  eb8*/    puVar7[0xb] = uStack_120;
/*  ec8-  ec8*/    puVar7[10] = uStack_128;
/*  ed8-  ed8*/    puVar7[0x11] = uStack_170;
/*  ee8-  ee8*/    puVar7[0x10] = uStack_178;
/*  ef8-  ef8*/    puVar7[0xe] = uStack_188;
/*  f08-  f08*/    puVar7[0xf] = uStack_180;
/*  f18-  f18*/    plStack_e0 = (undefined8 *)0x90;
/*  f40-  f40*/    puStack_e8 = puVar7;
/*  f28-  f40*/    solana_program::log::sol_log_data(&puStack_e8,1);
/*  f48-  f48*/    plVar16 = *(longlong **)(lVar18 + 0x188);
/*  f50-  f50*/    lVar8 = *plVar16;
/*  f70-  f70*/    pcVar13 = *(char **)(lVar18 + 0x180);
/*  f58-  f78*/    *plVar16 = lVar8 + 1;
/*  f58-  f80*/    if (lVar8 + 1 == 0) {
/*  5f8-  5f8*/LAB_ram_000395b8:
/*  5f8-  5f8*/                    /* WARNING: Subroutine does not return */
/*  5f8-  5f8*/      abort();
                  }
/*  f90-  f90*/    plVar6 = *(longlong **)(lVar18 + 400);
/*  f98-  f98*/    lVar8 = *plVar6;
/*  fa0-  fc8*/    *plVar6 = lVar8 + 1;
/*  5f8-  fd0*/    if (lVar8 + 1 == 0) goto LAB_ram_000395b8;
/* 1008- 1018*/    puVar19 = (undefined8 *)0x0;
/* 1000- 1018*/    if (puRam0000000300000000 + -0x20 <= puRam0000000300000000) {
/* 1000- 1030*/      puVar19 = puRam0000000300000000 + -0x20;
                  }
/* 1040- 1050*/    puVar7 = (undefined8 *)0x300007f00;
/* 1050- 1050*/    if (puRam0000000300000000 != (undefined8 *)0x0) {
/* 1058- 1058*/      puVar7 = puVar19;
                  }
/*  460- 1078*/    if (puVar7 < (undefined8 *)0x300000008) goto LAB_ram_00039420;
/* 1088- 1088*/    uVar1 = *(undefined1 *)(param_2 + 0x23);
/* 1090- 1090*/    uVar2 = *(undefined1 *)(lVar18 + 0x1aa);
/* 10a0- 10a0*/    uVar3 = *(undefined1 *)(lVar18 + 0x1a9);
/* 10b0- 10b0*/    uVar4 = *(undefined1 *)(lVar18 + 0x1a8);
/* 10c0- 10c0*/    uVar11 = *(undefined8 *)(lVar18 + 0x1a0);
/* 10d0- 10d0*/    uVar14 = *(undefined8 *)(lVar18 + 0x198);
/* 10f8- 10f8*/    puRam0000000300000000 = puVar7;
/* 10f8- 10f8*/    puVar7[1] = uVar10;
/* 1110- 1110*/    *puVar7 = 0xa2bf697f2006cb8e;
/* 1120- 1120*/    puVar7[5] = uStack_1b0;
/* 1130- 1130*/    puVar7[4] = uStack_1b8;
/* 1140- 1140*/    puVar7[3] = uStack_1c0;
/* 1150- 1150*/    puVar7[2] = uStack_1c8;
/* 1160- 1160*/    puVar7[9] = uStack_190;
/* 1170- 1170*/    puVar7[8] = uStack_198;
/* 1180- 1180*/    puVar7[7] = uStack_1a0;
/* 1190- 1190*/    puVar7[6] = uStack_1a8;
/* 11a0- 11a0*/    puVar7[10] = uStack_128;
/* 11b0- 11b0*/    puVar7[0xb] = uStack_120;
/* 11c0- 11c0*/    puVar7[0xc] = uStack_118;
/* 11d0- 11d0*/    puVar7[0xd] = uStack_110;
/* 11e0- 11e0*/    puVar7[0xe] = uStack_188;
/* 11f0- 11f0*/    puVar7[0xf] = uStack_180;
/* 1200- 1200*/    puVar7[0x10] = uStack_178;
/* 1210- 1210*/    puVar7[0x11] = uStack_170;
/* 1238- 1248*/    puVar19 = (undefined8 *)0x300008000;
/* 1248- 1248*/    if (puRam0000000300000000 != (undefined8 *)0x0) {
/* 1250- 1250*/      puVar19 = puRam0000000300000000;
                  }
/* 1268- 1280*/    puVar9 = (undefined8 *)0x0;
/* 1260- 1280*/    if (puVar19 + -0x13 <= puVar19) {
/* 1260- 1298*/      puVar9 = puVar19 + -0x13;
                  }
/* 12b0- 12b0*/    if (puVar9 < (undefined8 *)0x300000008) {
/* 17f0- 17f0*/                    /* WARNING: Subroutine does not return */
/* 17f0- 17f0*/      alloc::raw_vec::handle_error(1,0x98);
                  }
/* 12e0- 12e0*/    puRam0000000300000000 = puVar9;
/* 12e0- 12e0*/    *puVar9 = 0x1d9acb512ea545e4;
/* 12e8- 12e8*/    lVar18 = 0;
                  do {
/* 1308- 1318*/      *(undefined1 *)((longlong)puVar9 + lVar18 + 8) = *(undefined1 *)((longlong)puVar7 + lVar18);
/* 1320- 1320*/      lVar18 = lVar18 + 1;
/* 1328- 1328*/    } while (lVar18 != 0x90);
/* 1360- 1370*/    puVar19 = (undefined8 *)0x0;
/* 1358- 1370*/    if ((undefined8 *)((longlong)puRam0000000300000000 + -0x22) <= puRam0000000300000000) {
/* 1358- 1388*/      puVar19 = (undefined8 *)((longlong)puRam0000000300000000 + -0x22);
                  }
/* 1390- 13a0*/    plStack_78 = (undefined8 *)0x300007fde;
/* 13a0- 13a0*/    if (puRam0000000300000000 != (undefined8 *)0x0) {
/* 13a8- 13a8*/      plStack_78 = puVar19;
                  }
/* 13c8- 13c8*/    if (plStack_78 < (undefined8 *)0x300000008) {
/*  a00-  a00*/LAB_ram_000399c0:
/*  a10-  a10*/                    /* WARNING: Subroutine does not return */
/*  a10-  a10*/      alloc::alloc::handle_alloc_error(1,0x22);
                  }
/* 13f8- 13f8*/    uVar10 = *(undefined8 *)pcVar13;
/* 1400- 1400*/    uVar15 = *(undefined8 *)(pcVar13 + 8);
/* 1408- 1408*/    uVar17 = *(undefined8 *)(pcVar13 + 0x10);
/* 1418- 1418*/    puRam0000000300000000 = plStack_78;
/* 1410- 1418*/    plStack_78[3] = *(undefined8 *)(pcVar13 + 0x18);
/* 1420- 1420*/    plStack_78[2] = uVar17;
/* 1428- 1428*/    plStack_78[1] = uVar15;
/* 1430- 1430*/    *plStack_78 = uVar10;
/* 1438- 1438*/    *(undefined2 *)(plStack_78 + 4) = 1;
/* 1448- 1448*/    ppppcStack_70 = (char ****)0x1;
/* 1450- 1450*/    pcStack_80 = (char *)0x1;
/* 1498- 1498*/    solana_instruction::Instruction::new_with_bytes
/* 1460- 1498*/              (&puStack_e8,PUMP_PROGRAM_ID_1b79df,puVar9,0x98,&pcStack_80);
/* 1518- 1518*/    pppcStack_50 = &ppcStack_40;
/* 1530- 1530*/    puStack_30 = &uStack_19;
/* 1550- 1550*/    ppcStack_40 = (char **)0x1b6807;
/* 1560- 1560*/    uStack_48 = 2;
/* 1568- 1568*/    uStack_28 = 1;
/* 1570- 1570*/    uStack_38 = 0x11;
/* 15d0- 15d0*/    pcStack_80 = pcVar13;
/* 15d0- 15d0*/    plStack_78 = plVar16;
/* 15d0- 15d0*/    ppppcStack_70 = (char ****)plVar6;
/* 15d0- 15d0*/    uStack_68 = uVar14;
/* 15d0- 15d0*/    uStack_60 = uVar11;
/* 15d0- 15d0*/    uStack_58 = uVar4;
/* 15d0- 15d0*/    uStack_57 = uVar3;
/* 15d0- 15d0*/    uStack_56 = uVar2;
/* 15d0- 15d0*/    uStack_19 = uVar1;
/* 1460- 15d0*/    solana_program::program::invoke_signed(alStack_98,&puStack_e8,&pcStack_80,1);
/* 15f0- 15f0*/    if (alStack_98[0] == -0x7fffffffffffffe6) {
/* 1600- 1600*/      lVar18 = *plVar16;
/* 1608- 1610*/      *plVar16 = lVar18 + -1;
/* 1608- 1618*/      if (lVar18 + -1 == 0) {
/* 1620- 1630*/        plVar16[1] = plVar16[1] + -1;
                    }
/* 1640- 1648*/      pcVar13 = (char *)(*plVar6 + -1);
/* 1650- 1650*/      *plVar6 = (longlong)pcVar13;
/*  ca0-  ca0*/joined_r0x00039c60:
/*  ca0-  ca0*/      if (pcVar13 == (char *)0x0) {
/*  ca8-  cb0*/        pcVar13 = (char *)(plVar6[1] + -1);
/*  cb8-  cb8*/        plVar6[1] = (longlong)pcVar13;
                    }
/*  cc0-  cc0*/      uStack_1d8 = 2;
/*  260-  260*/      goto LAB_ram_00039220;
                  }
/* 1750- 1750*/    <anchor_lang::error::Error_as_core::convert::From<solana_program_error::ProgramError>>::from
/* 1738- 1750*/              (&uStack_1e8,alStack_98);
/* 1778- 1778*/    lVar18 = *plStack_78;
/* 1780- 1788*/    *plStack_78 = lVar18 + -1;
/* 1780- 1790*/    if (lVar18 + -1 == 0) {
/* 1798- 17a8*/      plStack_78[1] = plStack_78[1] + -1;
                  }
/* 17b0- 17b8*/    lVar18 = (longlong)*ppppcStack_70 + -1;
/* 17c0- 17c0*/    *ppppcStack_70 = (char ***)lVar18;
/* 17c8- 17c8*/    uStack_1d8 = uStack_1e8;
/* 17c8- 17c8*/    pcVar13 = pcStack_1e0;
/* 17c8- 17c8*/    plStack_d8 = (longlong *)ppppcStack_70;
                }
/* 1708- 1708*/  if (lVar18 == 0) {
/* 1710- 1720*/    plStack_d8[1] = plStack_d8[1] + -1;
                }
/*  260-  260*/LAB_ram_00039220:
/*  260-  260*/  param_1[1] = pcVar13;
/*  268-  268*/  *param_1 = uStack_1d8;
/*  270-  270*/  return;
              }
              
