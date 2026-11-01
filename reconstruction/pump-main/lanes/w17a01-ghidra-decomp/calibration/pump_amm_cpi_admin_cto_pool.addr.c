              
              void pump_recovered::pump_amm::cpi::admin_cto_pool
                             (undefined8 *param_1,longlong param_2,undefined8 *param_3,undefined1 param_4,
                             longlong param_5)
              
              {
                undefined1 uVar1;
                undefined1 uVar2;
                undefined1 uVar3;
                ulonglong uVar4;
                undefined8 uVar5;
                undefined1 *puVar6;
                longlong lVar7;
                longlong lVar8;
                undefined8 *puVar9;
                ulonglong uVar10;
                longlong *plVar11;
                longlong *plVar12;
                longlong *plVar13;
                longlong lVar14;
                longlong *plVar15;
                undefined8 *puVar16;
                undefined8 uVar17;
                undefined8 uVar18;
                undefined8 uVar19;
                undefined8 *puVar20;
                longlong lVar21;
                undefined8 *puStack_a8;
                longlong lStack_a0;
                undefined8 uStack_90;
                longlong *plStack_88;
                longlong lStack_80;
                longlong lStack_78;
                longlong lStack_70;
                undefined8 uStack_68;
                undefined8 *puStack_60;
                undefined8 uStack_58;
                undefined8 uStack_50;
                undefined8 uStack_48;
                undefined8 uStack_40;
                undefined8 uStack_38;
                longlong lStack_30;
                longlong lStack_28;
                longlong lStack_20;
                longlong lStack_18;
                longlong lStack_10;
                longlong lStack_8;
                
/*   38-   48*/  puVar9 = (undefined8 *)0x0;
/*   30-   48*/  if (puRam0000000300000000 + -0x20 <= puRam0000000300000000) {
/*   30-   60*/    puVar9 = puRam0000000300000000 + -0x20;
                }
/*   68-   78*/  puVar16 = (undefined8 *)0x300007f00;
/*   78-   78*/  if (puRam0000000300000000 != (undefined8 *)0x0) {
/*   80-   80*/    puVar16 = puVar9;
                }
/*   a0-   a0*/  if (puVar16 < (undefined8 *)0x300000008) {
/*  5d0-  5d0*/                    /* WARNING: Subroutine does not return */
/*  5d0-  5d0*/    alloc::raw_vec::handle_error(1,0x100);
                }
/*   a8-   a8*/  uVar5 = *(undefined8 *)(param_5 + -0xff8);
/*   b0-   b0*/  lVar7 = *(longlong *)(param_5 + -0x1000);
/*   e0-   e0*/  puRam0000000300000000 = puVar16;
/*   e0-   e0*/  *puVar16 = 0xbd31006897a53d2d;
/*   e8-   f0*/  puVar16[1] = *param_3;
/*   f8-  100*/  puVar16[2] = param_3[1];
/*  108-  110*/  puVar16[3] = param_3[2];
/*  118-  120*/  puVar16[4] = param_3[3];
/*  128-  128*/  *(undefined1 *)(puVar16 + 5) = param_4;
/*  130-  130*/  if (lVar7 == 0) {
/*  138-  138*/    *(undefined1 *)((longlong)puVar16 + 0x29) = 0;
/*  140-  140*/    uVar5 = 0x2a;
                }
                else {
/*  150-  150*/    *(undefined8 *)((longlong)puVar16 + 0x2a) = uVar5;
/*  158-  158*/    *(undefined1 *)((longlong)puVar16 + 0x29) = 1;
/*  160-  160*/    uVar5 = 0x32;
                }
/*  188-  188*/  <pump_recovered::pump_amm::internal::__cpi_client_accounts_admin_cto_pool::AdminCtoPool_as_anchor_lang::ToAccountMetas>::to_account_metas
/*  168-  188*/            (&lStack_80,param_2 + 0x48);
/*  198-  198*/  uVar4 = *(ulonglong *)(param_2 + 0x10);
/*  1a8-  1a8*/  if (uVar4 != 0) {
/*  3a0-  3a0*/    uVar18 = 0;
/*  3b0-  3b0*/    lStack_a0 = uVar4 * 0x22;
/*  3c8-  3c8*/    if (uVar4 < 0x3c3c3c3c3c3c3c4) {
/*  3e8-  3f8*/      puVar9 = (undefined8 *)0x300008000;
/*  3f8-  3f8*/      if (puRam0000000300000000 != (undefined8 *)0x0) {
/*  400-  400*/        puVar9 = puRam0000000300000000;
                    }
/*  410-  410*/      puVar20 = (undefined8 *)((longlong)puVar9 + uVar4 * -0x22);
/*  420-  420*/      uVar18 = 1;
/*  418-  430*/      puStack_a8 = (undefined8 *)0x0;
/*  430-  430*/      if (puVar20 <= puVar9) {
/*  448-  448*/        puStack_a8 = puVar20;
                    }
/*  460-  460*/      if ((undefined8 *)0x300000007 < puStack_a8) {
/*  470-  490*/        puVar6 = (undefined1 *)(*(longlong *)(param_2 + 8) + 0x29);
/*  4a8-  4a8*/        puVar9 = puStack_a8 + 4;
/*  4b8-  4b8*/        uVar10 = uVar4;
/*  4b8-  4b8*/        puRam0000000300000000 = puStack_a8;
                      do {
/*  4c0-  4c0*/          puVar20 = *(undefined8 **)(puVar6 + -0x29);
/*  4c8-  4c8*/          uVar19 = *puVar20;
/*  4d0-  4d0*/          uVar18 = puVar20[1];
/*  4d8-  4d8*/          uVar17 = puVar20[2];
/*  4e8-  4e8*/          uVar1 = puVar6[-1];
/*  4f0-  4f0*/          uVar2 = *puVar6;
/*  4e0-  4f8*/          puVar9[-1] = puVar20[3];
/*  500-  500*/          puVar9[-2] = uVar17;
/*  508-  508*/          puVar9[-3] = uVar18;
/*  510-  510*/          puVar9[-4] = uVar19;
/*  518-  518*/          *(undefined1 *)((longlong)puVar9 + 1) = uVar2;
/*  520-  520*/          *(undefined1 *)puVar9 = uVar1;
/*  528-  528*/          puVar6 = puVar6 + 0x30;
/*  530-  530*/          puVar9 = (undefined8 *)((longlong)puVar9 + 0x22);
/*  538-  538*/          uVar10 = uVar10 - 1;
/*  540-  540*/        } while (uVar10 != 0);
/*  560-  578*/        if ((ulonglong)(lStack_80 - lStack_70) < uVar4) {
/*  588-  5a0*/          alloc::raw_vec::RawVec<T,A>::reserve::do_reserve_and_handle(&lStack_80,lStack_70,uVar4);
                      }
/*  1e0-  1e0*/        goto LAB_ram_0010a2c0;
                    }
                  }
/*  5b8-  5b8*/                    /* WARNING: Subroutine does not return */
/*  5b8-  5b8*/    alloc::raw_vec::handle_error(uVar18);
                }
/*  1b8-  1b8*/  puStack_a8 = (undefined8 *)0x1;
/*  1c8-  1c8*/  lStack_a0 = 0;
/*  1e0-  1e0*/LAB_ram_0010a2c0:
/*  1e8-  210*/  memcpy(lStack_78 + lStack_70 * 0x22,puStack_a8,lStack_a0);
/*  218-  218*/  lStack_70 = lStack_70 + uVar4;
/*  230-  230*/  lStack_30 = lStack_80;
/*  240-  240*/  lStack_28 = lStack_78;
/*  250-  250*/  puVar9 = *(undefined8 **)(param_2 + 0x18);
/*  258-  258*/  uStack_50 = *puVar9;
/*  260-  260*/  uStack_48 = puVar9[1];
/*  268-  268*/  uStack_40 = puVar9[2];
/*  270-  270*/  uStack_38 = puVar9[3];
/*  2c0-  2c0*/  uStack_68 = 0x100;
/*  2e0-  2e0*/  puStack_60 = puVar16;
/*  2e0-  2e0*/  uStack_58 = uVar5;
/*  2e0-  2e0*/  lStack_20 = lStack_70;
/*  2e0-  2e0*/  <pump_recovered::set_creator::__cpi_client_accounts_set_creator::SetCreator_as_anchor_lang::ToAccountInfos>::to_account_infos
/*  168-  2e0*/            (&lStack_18,param_2 + 0x48);
/*  300-  300*/  lVar7 = *(longlong *)(param_2 + 8);
/*  308-  308*/  uVar4 = *(ulonglong *)(param_2 + 0x10);
/*  2f8-  310*/  if ((ulonglong)(lStack_18 - lStack_8) < uVar4) {
/*  320-  338*/    alloc::raw_vec::RawVec<T,A>::reserve::do_reserve_and_handle(&lStack_18,lStack_8,uVar4);
                }
/*  350-  350*/  lVar21 = lStack_8;
/*  350-  350*/  if (uVar4 != 0) {
/*  380-  380*/    lVar8 = 0;
                  do {
/*  720-  728*/      plVar11 = (longlong *)((undefined8 *)(lVar7 + lVar8))[1];
/*  730-  730*/      lVar14 = *plVar11;
/*  720-  758*/      uVar5 = *(undefined8 *)(lVar7 + lVar8);
/*  738-  760*/      *plVar11 = lVar14 + 1;
/*  738-  770*/      if (lVar14 + 1 == 0) goto LAB_ram_0010a850;
/*  780-  788*/      plVar15 = *(longlong **)(lVar7 + lVar8 + 0x10);
/*  790-  790*/      lVar14 = *plVar15;
/*  5d8-  798*/      *plVar15 = lVar14 + 1;
/*  5e0-  7a8*/      if (lVar14 + 1 == 0) goto LAB_ram_0010a850;
/*  360-  5f8*/      puVar9 = (undefined8 *)(lStack_10 + lStack_8 * 0x30 + lVar8);
/*  608-  608*/      lVar14 = lVar7 + lVar8;
/*  610-  610*/      uVar18 = *(undefined8 *)(lVar14 + 0x18);
/*  620-  620*/      uVar19 = *(undefined8 *)(lVar14 + 0x20);
/*  630-  630*/      uVar1 = *(undefined1 *)(lVar14 + 0x28);
/*  638-  638*/      uVar2 = *(undefined1 *)(lVar14 + 0x29);
/*  640-  648*/      *(undefined1 *)((longlong)puVar9 + 0x2a) = *(undefined1 *)(lVar14 + 0x2a);
/*  650-  650*/      *(undefined1 *)((longlong)puVar9 + 0x29) = uVar2;
/*  658-  658*/      *(undefined1 *)(puVar9 + 5) = uVar1;
/*  670-  670*/      puVar9[4] = uVar19;
/*  680-  680*/      puVar9[3] = uVar18;
/*  688-  688*/      puVar9[2] = plVar15;
/*  690-  690*/      puVar9[1] = plVar11;
/*  698-  698*/      *puVar9 = uVar5;
/*  6a0-  6a0*/      lVar8 = lVar8 + 0x30;
/*  6a8-  6a8*/      lVar21 = lVar21 + 1;
/*  6b8-  6b8*/      uVar4 = uVar4 - 1;
/*  6c0-  6c0*/    } while (uVar4 != 0);
                }
/*  6d8-  6d8*/  plVar11 = *(longlong **)(param_2 + 0x20);
/*  6e0-  6e0*/  lVar7 = *plVar11;
/*  7c0-  7c0*/  uVar5 = *(undefined8 *)(param_2 + 0x18);
/*  6e8-  7c8*/  *plVar11 = lVar7 + 1;
/*  7d0-  7d0*/  lStack_8 = lVar21;
/*  6e8-  7d0*/  if (lVar7 + 1 != 0) {
/*  7e0-  7e0*/    plVar15 = *(longlong **)(param_2 + 0x28);
/*  7e8-  7e8*/    lVar7 = *plVar15;
/*  7f0-  810*/    *plVar15 = lVar7 + 1;
/*  7f0-  818*/    if (lVar7 + 1 != 0) {
/*  828-  828*/      uVar1 = *(undefined1 *)(param_2 + 0x42);
/*  838-  838*/      uVar2 = *(undefined1 *)(param_2 + 0x41);
/*  848-  848*/      uVar3 = *(undefined1 *)(param_2 + 0x40);
/*  858-  858*/      uVar18 = *(undefined8 *)(param_2 + 0x38);
/*  860-  860*/      uVar19 = *(undefined8 *)(param_2 + 0x30);
/*  870-  870*/      lVar7 = lStack_10;
/*  870-  870*/      if (lVar21 == lStack_18) {
/*  880-  8a0*/        alloc::raw_vec::RawVec<T,A>::grow_one(&lStack_18);
/*  8c8-  8c8*/        lVar7 = lStack_10;
                    }
/*  8d8-  8e8*/      puVar9 = (undefined8 *)(lVar7 + lVar21 * 0x30);
/*  8f8-  8f8*/      *(undefined1 *)((longlong)puVar9 + 0x2a) = uVar1;
/*  908-  908*/      *(undefined1 *)((longlong)puVar9 + 0x29) = uVar2;
/*  918-  918*/      *(undefined1 *)(puVar9 + 5) = uVar3;
/*  920-  920*/      puVar9[4] = uVar18;
/*  928-  928*/      puVar9[3] = uVar19;
/*  930-  930*/      puVar9[2] = plVar15;
/*  938-  938*/      puVar9[1] = plVar11;
/*  940-  940*/      *puVar9 = uVar5;
/*  968-  968*/      lVar21 = lVar21 + 1;
/*  988-  988*/      plVar11 = &lStack_80;
/*  978-  9a8*/      solana_program::program::invoke_signed(&lStack_18,plVar11,lVar7,lVar21);
/*  9b0-  9d0*/      uVar5 = 2;
/*  9d0-  9d0*/      if (lStack_18 != -0x7fffffffffffffe6) {
/*  9f8-  9f8*/        <anchor_lang::error::Error_as_core::convert::From<solana_program_error::ProgramError>>::from
/*  9e0-  9f8*/                  (&uStack_90,&lStack_18);
/*  a08-  a08*/        uVar5 = uStack_90;
/*  a08-  a08*/        plVar11 = plStack_88;
                    }
/*  a18-  a18*/      if (lVar21 != 0) {
/*  a20-  a20*/        plVar15 = (longlong *)(lVar7 + 0x10);
                      do {
/*  a98-  a98*/          plVar12 = (longlong *)*plVar15;
/*  aa0-  aa0*/          plVar13 = (longlong *)plVar15[-1];
/*  aa8-  aa8*/          lVar7 = *plVar13;
/*  ab0-  ab8*/          *plVar13 = lVar7 + -1;
/*  ab0-  ac0*/          if (lVar7 + -1 == 0) {
/*  ac8-  ad8*/            plVar13[1] = plVar13[1] + -1;
                        }
/*  ae0-  ae0*/          lVar7 = *plVar12;
/*  ae8-  af0*/          *plVar12 = lVar7 + -1;
/*  ae8-  af8*/          if (lVar7 + -1 == 0) {
/*  b00-  b10*/            plVar12[1] = plVar12[1] + -1;
                        }
/*  a30-  a30*/          plVar15 = plVar15 + 6;
/*  a38-  a38*/          lVar21 = lVar21 + -1;
/*  a40-  a40*/        } while (lVar21 != 0);
                    }
/*  a48-  a48*/      plVar15 = *(longlong **)(param_2 + 0x58);
/*  a50-  a50*/      plVar12 = *(longlong **)(param_2 + 0x50);
/*  a58-  a58*/      lVar7 = *plVar12;
/*  a60-  a68*/      *plVar12 = lVar7 + -1;
/*  a60-  a70*/      if (lVar7 + -1 == 0) {
/*  a78-  a88*/        plVar12[1] = plVar12[1] + -1;
                    }
/*  b20-  b20*/      lVar7 = *plVar15;
/*  b28-  b30*/      *plVar15 = lVar7 + -1;
/*  b28-  b38*/      if (lVar7 + -1 == 0) {
/*  b40-  b50*/        plVar15[1] = plVar15[1] + -1;
                    }
/*  b58-  b58*/      plVar15 = *(longlong **)(param_2 + 0x88);
/*  b60-  b60*/      plVar12 = *(longlong **)(param_2 + 0x80);
/*  b68-  b68*/      lVar7 = *plVar12;
/*  b70-  b78*/      *plVar12 = lVar7 + -1;
/*  b70-  b80*/      if (lVar7 + -1 == 0) {
/*  b88-  b98*/        plVar12[1] = plVar12[1] + -1;
                    }
/*  ba0-  ba0*/      lVar7 = *plVar15;
/*  ba8-  bb0*/      *plVar15 = lVar7 + -1;
/*  ba8-  bb8*/      if (lVar7 + -1 == 0) {
/*  bc0-  bd0*/        plVar15[1] = plVar15[1] + -1;
                    }
/*  bd8-  bd8*/      plVar15 = *(longlong **)(param_2 + 0xb8);
/*  be0-  be0*/      plVar12 = *(longlong **)(param_2 + 0xb0);
/*  be8-  be8*/      lVar7 = *plVar12;
/*  bf0-  bf8*/      *plVar12 = lVar7 + -1;
/*  bf0-  c00*/      if (lVar7 + -1 == 0) {
/*  c08-  c18*/        plVar12[1] = plVar12[1] + -1;
                    }
/*  c20-  c20*/      lVar7 = *plVar15;
/*  c28-  c30*/      *plVar15 = lVar7 + -1;
/*  c28-  c38*/      if (lVar7 + -1 == 0) {
/*  c40-  c50*/        plVar15[1] = plVar15[1] + -1;
                    }
/*  c58-  c58*/      plVar15 = *(longlong **)(param_2 + 0xe8);
/*  c60-  c60*/      plVar12 = *(longlong **)(param_2 + 0xe0);
/*  c68-  c68*/      lVar7 = *plVar12;
/*  c70-  c78*/      *plVar12 = lVar7 + -1;
/*  c70-  c80*/      if (lVar7 + -1 == 0) {
/*  c88-  c98*/        plVar12[1] = plVar12[1] + -1;
                    }
/*  ca0-  ca0*/      lVar7 = *plVar15;
/*  ca8-  cb0*/      *plVar15 = lVar7 + -1;
/*  ca8-  cb8*/      if (lVar7 + -1 == 0) {
/*  cc0-  cd0*/        plVar15[1] = plVar15[1] + -1;
                    }
/*  cd8-  cd8*/      plVar15 = *(longlong **)(param_2 + 0x118);
/*  ce0-  ce0*/      plVar12 = *(longlong **)(param_2 + 0x110);
/*  ce8-  ce8*/      lVar7 = *plVar12;
/*  cf0-  cf8*/      *plVar12 = lVar7 + -1;
/*  cf0-  d00*/      if (lVar7 + -1 == 0) {
/*  d08-  d18*/        plVar12[1] = plVar12[1] + -1;
                    }
/*  d20-  d20*/      lVar7 = *plVar15;
/*  d28-  d30*/      *plVar15 = lVar7 + -1;
/*  d28-  d38*/      if (lVar7 + -1 == 0) {
/*  d40-  d50*/        plVar15[1] = plVar15[1] + -1;
                    }
/*  d58-  d58*/      plVar15 = *(longlong **)(param_2 + 0x148);
/*  d60-  d60*/      plVar12 = *(longlong **)(param_2 + 0x140);
/*  d68-  d68*/      lVar7 = *plVar12;
/*  d70-  d78*/      *plVar12 = lVar7 + -1;
/*  d70-  d80*/      if (lVar7 + -1 == 0) {
/*  d88-  d98*/        plVar12[1] = plVar12[1] + -1;
                    }
/*  da0-  da0*/      lVar7 = *plVar15;
/*  da8-  db0*/      *plVar15 = lVar7 + -1;
/*  da8-  db8*/      if (lVar7 + -1 == 0) {
/*  dc0-  dd0*/        plVar15[1] = plVar15[1] + -1;
                    }
/*  dd8-  dd8*/      plVar15 = *(longlong **)(param_2 + 0x178);
/*  de0-  de0*/      plVar12 = *(longlong **)(param_2 + 0x170);
/*  de8-  de8*/      lVar7 = *plVar12;
/*  df0-  df8*/      *plVar12 = lVar7 + -1;
/*  df0-  e00*/      if (lVar7 + -1 == 0) {
/*  e08-  e18*/        plVar12[1] = plVar12[1] + -1;
                    }
/*  e20-  e20*/      lVar7 = *plVar15;
/*  e28-  e30*/      *plVar15 = lVar7 + -1;
/*  e28-  e38*/      if (lVar7 + -1 == 0) {
/*  e40-  e50*/        plVar15[1] = plVar15[1] + -1;
                    }
/*  e58-  e58*/      lVar7 = *(longlong *)(param_2 + 0x10);
/*  e60-  e60*/      if (lVar7 != 0) {
/*  e70-  e78*/        puVar9 = (undefined8 *)(*(longlong *)(param_2 + 8) + 0x10);
                      do {
/*  ef8-  ef8*/          plVar12 = (longlong *)*puVar9;
/*  f00-  f00*/          plVar15 = (longlong *)puVar9[-1];
/*  f08-  f08*/          lVar21 = *plVar15;
/*  f10-  f18*/          *plVar15 = lVar21 + -1;
/*  f10-  f20*/          if (lVar21 + -1 == 0) {
/*  f28-  f38*/            plVar15[1] = plVar15[1] + -1;
                        }
/*  f40-  f40*/          lVar21 = *plVar12;
/*  f48-  f50*/          *plVar12 = lVar21 + -1;
/*  f48-  f58*/          if (lVar21 + -1 == 0) {
/*  f60-  f70*/            plVar12[1] = plVar12[1] + -1;
                        }
/*  e88-  e88*/          puVar9 = puVar9 + 6;
/*  e90-  e90*/          lVar7 = lVar7 + -1;
/*  e98-  e98*/        } while (lVar7 != 0);
                    }
/*  ea8-  ea8*/      plVar15 = *(longlong **)(param_2 + 0x28);
/*  eb0-  eb0*/      plVar12 = *(longlong **)(param_2 + 0x20);
/*  eb8-  eb8*/      lVar7 = *plVar12;
/*  ec0-  ec8*/      *plVar12 = lVar7 + -1;
/*  ec0-  ed0*/      if (lVar7 + -1 == 0) {
/*  ed8-  ee8*/        plVar12[1] = plVar12[1] + -1;
                    }
/*  f80-  f80*/      lVar7 = *plVar15;
/*  f88-  f90*/      *plVar15 = lVar7 + -1;
/*  f88-  f98*/      if (lVar7 + -1 == 0) {
/*  fa0-  fb0*/        plVar15[1] = plVar15[1] + -1;
                    }
/*  fc0-  fc0*/      param_1[1] = plVar11;
/*  fc8-  fc8*/      *param_1 = uVar5;
/*  fd0-  fd0*/      return;
                  }
                }
/*  770-  770*/LAB_ram_0010a850:
/*  770-  770*/                    /* WARNING: Subroutine does not return */
/*  770-  770*/  abort();
              }
              
