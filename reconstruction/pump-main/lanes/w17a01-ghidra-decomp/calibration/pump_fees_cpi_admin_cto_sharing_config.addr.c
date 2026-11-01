              
              void pump_recovered::pump_fees::cpi::admin_cto_sharing_config
                             (undefined8 *param_1,longlong param_2,char *param_3)
              
              {
                char cVar1;
                undefined1 uVar2;
                undefined1 uVar3;
                undefined1 uVar4;
                ulonglong uVar5;
                undefined1 *puVar6;
                longlong lVar7;
                undefined8 *puVar8;
                ulonglong uVar9;
                longlong *plVar10;
                longlong *plVar11;
                longlong *plVar12;
                longlong lVar13;
                longlong *plVar14;
                undefined8 *puVar15;
                longlong lVar16;
                undefined8 uVar17;
                undefined8 uVar18;
                undefined8 uVar19;
                undefined8 *puVar20;
                longlong lVar21;
                undefined8 uVar22;
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
                
/*   30-   40*/  puVar8 = (undefined8 *)0x0;
/*   28-   40*/  if (puRam0000000300000000 + -0x20 <= puRam0000000300000000) {
/*   28-   58*/    puVar8 = puRam0000000300000000 + -0x20;
                }
/*   60-   70*/  puVar15 = (undefined8 *)0x300007f00;
/*   70-   70*/  if (puRam0000000300000000 != (undefined8 *)0x0) {
/*   78-   78*/    puVar15 = puVar8;
                }
/*   90-   90*/  if (puVar15 < (undefined8 *)0x300000008) {
/*  5c0-  5c0*/                    /* WARNING: Subroutine does not return */
/*  5c0-  5c0*/    alloc::raw_vec::handle_error(1,0x100);
                }
/*   98-   98*/  cVar1 = *param_3;
/*   c8-   c8*/  puRam0000000300000000 = puVar15;
/*   c8-   c8*/  *puVar15 = 0x25b68a409c90643c;
/*   e0-   e0*/  if (cVar1 == '\0') {
/*   e8-   e8*/    *(undefined1 *)(puVar15 + 1) = 0;
/*   f0-   f0*/    uVar22 = 9;
                }
                else {
/*  108-  108*/    *(undefined1 *)(puVar15 + 1) = 1;
/*  100-  118*/    *(undefined8 *)((longlong)puVar15 + 9) = *(undefined8 *)(param_3 + 1);
/*  120-  128*/    *(undefined8 *)((longlong)puVar15 + 0x11) = *(undefined8 *)(param_3 + 9);
/*  130-  138*/    *(undefined8 *)((longlong)puVar15 + 0x19) = *(undefined8 *)(param_3 + 0x11);
/*  140-  148*/    *(undefined8 *)((longlong)puVar15 + 0x21) = *(undefined8 *)(param_3 + 0x19);
/*  150-  150*/    uVar22 = 0x29;
                }
/*  178-  178*/  <pump_recovered::pump_fees::internal::__cpi_client_accounts_admin_cto_sharing_config::AdminCtoSharingConfig_as_anchor_lang::ToAccountMetas>::to_account_metas
/*  158-  178*/            (&lStack_80,param_2 + 0x48);
/*  188-  188*/  uVar5 = *(ulonglong *)(param_2 + 0x10);
/*  198-  198*/  if (uVar5 != 0) {
/*  390-  390*/    uVar18 = 0;
/*  3a0-  3a0*/    lStack_a0 = uVar5 * 0x22;
/*  3b8-  3b8*/    if (uVar5 < 0x3c3c3c3c3c3c3c4) {
/*  3d8-  3e8*/      puVar8 = (undefined8 *)0x300008000;
/*  3e8-  3e8*/      if (puRam0000000300000000 != (undefined8 *)0x0) {
/*  3f0-  3f0*/        puVar8 = puRam0000000300000000;
                    }
/*  400-  400*/      puVar20 = (undefined8 *)((longlong)puVar8 + uVar5 * -0x22);
/*  410-  410*/      uVar18 = 1;
/*  408-  420*/      puStack_a8 = (undefined8 *)0x0;
/*  420-  420*/      if (puVar20 <= puVar8) {
/*  438-  438*/        puStack_a8 = puVar20;
                    }
/*  450-  450*/      if ((undefined8 *)0x300000007 < puStack_a8) {
/*  460-  480*/        puVar6 = (undefined1 *)(*(longlong *)(param_2 + 8) + 0x29);
/*  498-  498*/        puVar8 = puStack_a8 + 4;
/*  4a8-  4a8*/        uVar9 = uVar5;
/*  4a8-  4a8*/        puRam0000000300000000 = puStack_a8;
                      do {
/*  4b0-  4b0*/          puVar20 = *(undefined8 **)(puVar6 + -0x29);
/*  4b8-  4b8*/          uVar19 = *puVar20;
/*  4c0-  4c0*/          uVar18 = puVar20[1];
/*  4c8-  4c8*/          uVar17 = puVar20[2];
/*  4d8-  4d8*/          uVar2 = puVar6[-1];
/*  4e0-  4e0*/          uVar3 = *puVar6;
/*  4d0-  4e8*/          puVar8[-1] = puVar20[3];
/*  4f0-  4f0*/          puVar8[-2] = uVar17;
/*  4f8-  4f8*/          puVar8[-3] = uVar18;
/*  500-  500*/          puVar8[-4] = uVar19;
/*  508-  508*/          *(undefined1 *)((longlong)puVar8 + 1) = uVar3;
/*  510-  510*/          *(undefined1 *)puVar8 = uVar2;
/*  518-  518*/          puVar6 = puVar6 + 0x30;
/*  520-  520*/          puVar8 = (undefined8 *)((longlong)puVar8 + 0x22);
/*  528-  528*/          uVar9 = uVar9 - 1;
/*  530-  530*/        } while (uVar9 != 0);
/*  550-  568*/        if ((ulonglong)(lStack_80 - lStack_70) < uVar5) {
/*  578-  590*/          alloc::raw_vec::RawVec<T,A>::reserve::do_reserve_and_handle(&lStack_80,lStack_70,uVar5);
                      }
/*  1d0-  1d0*/        goto LAB_ram_001168e8;
                    }
                  }
/*  5a8-  5a8*/                    /* WARNING: Subroutine does not return */
/*  5a8-  5a8*/    alloc::raw_vec::handle_error(uVar18);
                }
/*  1a8-  1a8*/  puStack_a8 = (undefined8 *)0x1;
/*  1b8-  1b8*/  lStack_a0 = 0;
/*  1d0-  1d0*/LAB_ram_001168e8:
/*  1d8-  200*/  memcpy(lStack_78 + lStack_70 * 0x22,puStack_a8,lStack_a0);
/*  208-  208*/  lStack_70 = lStack_70 + uVar5;
/*  220-  220*/  lStack_30 = lStack_80;
/*  230-  230*/  lStack_28 = lStack_78;
/*  240-  240*/  puVar8 = *(undefined8 **)(param_2 + 0x18);
/*  248-  248*/  uStack_50 = *puVar8;
/*  250-  250*/  uStack_48 = puVar8[1];
/*  258-  258*/  uStack_40 = puVar8[2];
/*  260-  260*/  uStack_38 = puVar8[3];
/*  2b0-  2b0*/  uStack_68 = 0x100;
/*  2d0-  2d0*/  puStack_60 = puVar15;
/*  2d0-  2d0*/  uStack_58 = uVar22;
/*  2d0-  2d0*/  lStack_20 = lStack_70;
/*  2d0-  2d0*/  <pump_recovered::set_creator::__cpi_client_accounts_set_creator::SetCreator_as_anchor_lang::ToAccountInfos>::to_account_infos
/*  158-  2d0*/            (&lStack_18,param_2 + 0x48);
/*  2f0-  2f0*/  lVar16 = *(longlong *)(param_2 + 8);
/*  2f8-  2f8*/  uVar5 = *(ulonglong *)(param_2 + 0x10);
/*  2e8-  300*/  if ((ulonglong)(lStack_18 - lStack_8) < uVar5) {
/*  310-  328*/    alloc::raw_vec::RawVec<T,A>::reserve::do_reserve_and_handle(&lStack_18,lStack_8,uVar5);
                }
/*  340-  340*/  lVar21 = lStack_8;
/*  340-  340*/  if (uVar5 != 0) {
/*  370-  370*/    lVar7 = 0;
                  do {
/*  710-  718*/      plVar10 = (longlong *)((undefined8 *)(lVar16 + lVar7))[1];
/*  720-  720*/      lVar13 = *plVar10;
/*  710-  748*/      uVar22 = *(undefined8 *)(lVar16 + lVar7);
/*  728-  750*/      *plVar10 = lVar13 + 1;
/*  728-  760*/      if (lVar13 + 1 == 0) goto LAB_ram_00116e78;
/*  770-  778*/      plVar14 = *(longlong **)(lVar16 + lVar7 + 0x10);
/*  780-  780*/      lVar13 = *plVar14;
/*  5c8-  788*/      *plVar14 = lVar13 + 1;
/*  5d0-  798*/      if (lVar13 + 1 == 0) goto LAB_ram_00116e78;
/*  350-  5e8*/      puVar8 = (undefined8 *)(lStack_10 + lStack_8 * 0x30 + lVar7);
/*  5f8-  5f8*/      lVar13 = lVar16 + lVar7;
/*  600-  600*/      uVar18 = *(undefined8 *)(lVar13 + 0x18);
/*  610-  610*/      uVar19 = *(undefined8 *)(lVar13 + 0x20);
/*  620-  620*/      uVar2 = *(undefined1 *)(lVar13 + 0x28);
/*  628-  628*/      uVar3 = *(undefined1 *)(lVar13 + 0x29);
/*  630-  638*/      *(undefined1 *)((longlong)puVar8 + 0x2a) = *(undefined1 *)(lVar13 + 0x2a);
/*  640-  640*/      *(undefined1 *)((longlong)puVar8 + 0x29) = uVar3;
/*  648-  648*/      *(undefined1 *)(puVar8 + 5) = uVar2;
/*  660-  660*/      puVar8[4] = uVar19;
/*  670-  670*/      puVar8[3] = uVar18;
/*  678-  678*/      puVar8[2] = plVar14;
/*  680-  680*/      puVar8[1] = plVar10;
/*  688-  688*/      *puVar8 = uVar22;
/*  690-  690*/      lVar7 = lVar7 + 0x30;
/*  698-  698*/      lVar21 = lVar21 + 1;
/*  6a8-  6a8*/      uVar5 = uVar5 - 1;
/*  6b0-  6b0*/    } while (uVar5 != 0);
                }
/*  6c8-  6c8*/  plVar10 = *(longlong **)(param_2 + 0x20);
/*  6d0-  6d0*/  lVar16 = *plVar10;
/*  7b0-  7b0*/  uVar22 = *(undefined8 *)(param_2 + 0x18);
/*  6d8-  7b8*/  *plVar10 = lVar16 + 1;
/*  7c0-  7c0*/  lStack_8 = lVar21;
/*  6d8-  7c0*/  if (lVar16 + 1 != 0) {
/*  7d0-  7d0*/    plVar14 = *(longlong **)(param_2 + 0x28);
/*  7d8-  7d8*/    lVar16 = *plVar14;
/*  7e0-  800*/    *plVar14 = lVar16 + 1;
/*  7e0-  808*/    if (lVar16 + 1 != 0) {
/*  818-  818*/      uVar2 = *(undefined1 *)(param_2 + 0x42);
/*  828-  828*/      uVar3 = *(undefined1 *)(param_2 + 0x41);
/*  838-  838*/      uVar4 = *(undefined1 *)(param_2 + 0x40);
/*  848-  848*/      uVar18 = *(undefined8 *)(param_2 + 0x38);
/*  850-  850*/      uVar19 = *(undefined8 *)(param_2 + 0x30);
/*  860-  860*/      lVar16 = lStack_10;
/*  860-  860*/      if (lVar21 == lStack_18) {
/*  870-  890*/        alloc::raw_vec::RawVec<T,A>::grow_one(&lStack_18);
/*  8b8-  8b8*/        lVar16 = lStack_10;
                    }
/*  8c8-  8d8*/      puVar8 = (undefined8 *)(lVar16 + lVar21 * 0x30);
/*  8e8-  8e8*/      *(undefined1 *)((longlong)puVar8 + 0x2a) = uVar2;
/*  8f8-  8f8*/      *(undefined1 *)((longlong)puVar8 + 0x29) = uVar3;
/*  908-  908*/      *(undefined1 *)(puVar8 + 5) = uVar4;
/*  910-  910*/      puVar8[4] = uVar18;
/*  918-  918*/      puVar8[3] = uVar19;
/*  920-  920*/      puVar8[2] = plVar14;
/*  928-  928*/      puVar8[1] = plVar10;
/*  930-  930*/      *puVar8 = uVar22;
/*  958-  958*/      lVar21 = lVar21 + 1;
/*  978-  978*/      plVar10 = &lStack_80;
/*  968-  998*/      solana_program::program::invoke_signed(&lStack_18,plVar10,lVar16,lVar21);
/*  9a0-  9c0*/      uVar22 = 2;
/*  9c0-  9c0*/      if (lStack_18 != -0x7fffffffffffffe6) {
/*  9e8-  9e8*/        <anchor_lang::error::Error_as_core::convert::From<solana_program_error::ProgramError>>::from
/*  9d0-  9e8*/                  (&uStack_90,&lStack_18);
/*  9f8-  9f8*/        uVar22 = uStack_90;
/*  9f8-  9f8*/        plVar10 = plStack_88;
                    }
/*  a08-  a08*/      if (lVar21 != 0) {
/*  a10-  a10*/        plVar14 = (longlong *)(lVar16 + 0x10);
                      do {
/*  a88-  a88*/          plVar11 = (longlong *)*plVar14;
/*  a90-  a90*/          plVar12 = (longlong *)plVar14[-1];
/*  a98-  a98*/          lVar16 = *plVar12;
/*  aa0-  aa8*/          *plVar12 = lVar16 + -1;
/*  aa0-  ab0*/          if (lVar16 + -1 == 0) {
/*  ab8-  ac8*/            plVar12[1] = plVar12[1] + -1;
                        }
/*  ad0-  ad0*/          lVar16 = *plVar11;
/*  ad8-  ae0*/          *plVar11 = lVar16 + -1;
/*  ad8-  ae8*/          if (lVar16 + -1 == 0) {
/*  af0-  b00*/            plVar11[1] = plVar11[1] + -1;
                        }
/*  a20-  a20*/          plVar14 = plVar14 + 6;
/*  a28-  a28*/          lVar21 = lVar21 + -1;
/*  a30-  a30*/        } while (lVar21 != 0);
                    }
/*  a38-  a38*/      plVar14 = *(longlong **)(param_2 + 0x58);
/*  a40-  a40*/      plVar11 = *(longlong **)(param_2 + 0x50);
/*  a48-  a48*/      lVar16 = *plVar11;
/*  a50-  a58*/      *plVar11 = lVar16 + -1;
/*  a50-  a60*/      if (lVar16 + -1 == 0) {
/*  a68-  a78*/        plVar11[1] = plVar11[1] + -1;
                    }
/*  b10-  b10*/      lVar16 = *plVar14;
/*  b18-  b20*/      *plVar14 = lVar16 + -1;
/*  b18-  b28*/      if (lVar16 + -1 == 0) {
/*  b30-  b40*/        plVar14[1] = plVar14[1] + -1;
                    }
/*  b48-  b48*/      plVar14 = *(longlong **)(param_2 + 0x88);
/*  b50-  b50*/      plVar11 = *(longlong **)(param_2 + 0x80);
/*  b58-  b58*/      lVar16 = *plVar11;
/*  b60-  b68*/      *plVar11 = lVar16 + -1;
/*  b60-  b70*/      if (lVar16 + -1 == 0) {
/*  b78-  b88*/        plVar11[1] = plVar11[1] + -1;
                    }
/*  b90-  b90*/      lVar16 = *plVar14;
/*  b98-  ba0*/      *plVar14 = lVar16 + -1;
/*  b98-  ba8*/      if (lVar16 + -1 == 0) {
/*  bb0-  bc0*/        plVar14[1] = plVar14[1] + -1;
                    }
/*  bc8-  bc8*/      plVar14 = *(longlong **)(param_2 + 0xb8);
/*  bd0-  bd0*/      plVar11 = *(longlong **)(param_2 + 0xb0);
/*  bd8-  bd8*/      lVar16 = *plVar11;
/*  be0-  be8*/      *plVar11 = lVar16 + -1;
/*  be0-  bf0*/      if (lVar16 + -1 == 0) {
/*  bf8-  c08*/        plVar11[1] = plVar11[1] + -1;
                    }
/*  c10-  c10*/      lVar16 = *plVar14;
/*  c18-  c20*/      *plVar14 = lVar16 + -1;
/*  c18-  c28*/      if (lVar16 + -1 == 0) {
/*  c30-  c40*/        plVar14[1] = plVar14[1] + -1;
                    }
/*  c48-  c48*/      plVar14 = *(longlong **)(param_2 + 0xe8);
/*  c50-  c50*/      plVar11 = *(longlong **)(param_2 + 0xe0);
/*  c58-  c58*/      lVar16 = *plVar11;
/*  c60-  c68*/      *plVar11 = lVar16 + -1;
/*  c60-  c70*/      if (lVar16 + -1 == 0) {
/*  c78-  c88*/        plVar11[1] = plVar11[1] + -1;
                    }
/*  c90-  c90*/      lVar16 = *plVar14;
/*  c98-  ca0*/      *plVar14 = lVar16 + -1;
/*  c98-  ca8*/      if (lVar16 + -1 == 0) {
/*  cb0-  cc0*/        plVar14[1] = plVar14[1] + -1;
                    }
/*  cc8-  cc8*/      plVar14 = *(longlong **)(param_2 + 0x118);
/*  cd0-  cd0*/      plVar11 = *(longlong **)(param_2 + 0x110);
/*  cd8-  cd8*/      lVar16 = *plVar11;
/*  ce0-  ce8*/      *plVar11 = lVar16 + -1;
/*  ce0-  cf0*/      if (lVar16 + -1 == 0) {
/*  cf8-  d08*/        plVar11[1] = plVar11[1] + -1;
                    }
/*  d10-  d10*/      lVar16 = *plVar14;
/*  d18-  d20*/      *plVar14 = lVar16 + -1;
/*  d18-  d28*/      if (lVar16 + -1 == 0) {
/*  d30-  d40*/        plVar14[1] = plVar14[1] + -1;
                    }
/*  d48-  d48*/      plVar14 = *(longlong **)(param_2 + 0x148);
/*  d50-  d50*/      plVar11 = *(longlong **)(param_2 + 0x140);
/*  d58-  d58*/      lVar16 = *plVar11;
/*  d60-  d68*/      *plVar11 = lVar16 + -1;
/*  d60-  d70*/      if (lVar16 + -1 == 0) {
/*  d78-  d88*/        plVar11[1] = plVar11[1] + -1;
                    }
/*  d90-  d90*/      lVar16 = *plVar14;
/*  d98-  da0*/      *plVar14 = lVar16 + -1;
/*  d98-  da8*/      if (lVar16 + -1 == 0) {
/*  db0-  dc0*/        plVar14[1] = plVar14[1] + -1;
                    }
/*  dc8-  dc8*/      plVar14 = *(longlong **)(param_2 + 0x178);
/*  dd0-  dd0*/      plVar11 = *(longlong **)(param_2 + 0x170);
/*  dd8-  dd8*/      lVar16 = *plVar11;
/*  de0-  de8*/      *plVar11 = lVar16 + -1;
/*  de0-  df0*/      if (lVar16 + -1 == 0) {
/*  df8-  e08*/        plVar11[1] = plVar11[1] + -1;
                    }
/*  e10-  e10*/      lVar16 = *plVar14;
/*  e18-  e20*/      *plVar14 = lVar16 + -1;
/*  e18-  e28*/      if (lVar16 + -1 == 0) {
/*  e30-  e40*/        plVar14[1] = plVar14[1] + -1;
                    }
/*  e48-  e48*/      lVar16 = *(longlong *)(param_2 + 0x10);
/*  e50-  e50*/      if (lVar16 != 0) {
/*  e60-  e68*/        puVar8 = (undefined8 *)(*(longlong *)(param_2 + 8) + 0x10);
                      do {
/*  ee8-  ee8*/          plVar11 = (longlong *)*puVar8;
/*  ef0-  ef0*/          plVar14 = (longlong *)puVar8[-1];
/*  ef8-  ef8*/          lVar21 = *plVar14;
/*  f00-  f08*/          *plVar14 = lVar21 + -1;
/*  f00-  f10*/          if (lVar21 + -1 == 0) {
/*  f18-  f28*/            plVar14[1] = plVar14[1] + -1;
                        }
/*  f30-  f30*/          lVar21 = *plVar11;
/*  f38-  f40*/          *plVar11 = lVar21 + -1;
/*  f38-  f48*/          if (lVar21 + -1 == 0) {
/*  f50-  f60*/            plVar11[1] = plVar11[1] + -1;
                        }
/*  e78-  e78*/          puVar8 = puVar8 + 6;
/*  e80-  e80*/          lVar16 = lVar16 + -1;
/*  e88-  e88*/        } while (lVar16 != 0);
                    }
/*  e98-  e98*/      plVar14 = *(longlong **)(param_2 + 0x28);
/*  ea0-  ea0*/      plVar11 = *(longlong **)(param_2 + 0x20);
/*  ea8-  ea8*/      lVar16 = *plVar11;
/*  eb0-  eb8*/      *plVar11 = lVar16 + -1;
/*  eb0-  ec0*/      if (lVar16 + -1 == 0) {
/*  ec8-  ed8*/        plVar11[1] = plVar11[1] + -1;
                    }
/*  f70-  f70*/      lVar16 = *plVar14;
/*  f78-  f80*/      *plVar14 = lVar16 + -1;
/*  f78-  f90*/      if (lVar16 + -1 == 0) {
/*  f98-  fa8*/        plVar14[1] = plVar14[1] + -1;
                    }
/*  fb0-  fb0*/      param_1[1] = plVar10;
/*  fb8-  fb8*/      *param_1 = uVar22;
/*  fc0-  fc0*/      return;
                  }
                }
/*  760-  760*/LAB_ram_00116e78:
/*  760-  760*/                    /* WARNING: Subroutine does not return */
/*  760-  760*/  abort();
              }
              
