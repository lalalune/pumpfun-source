/* 6398*/          goto joined_r0x00028da8;
/* 60f8*/          bVar102 = true;
/* 6100*/          bVar101 = false;
/* 5c60*/          if (lVar120 == 0) goto LAB_ram_00028670;
/* 6120*/LAB_ram_00028b30:
/* 61d8*/          pump_recovered::creator::collect_creator_fee::collect
/* 6150*/                    (&ppppppplStack_2d0,plVar81,plVar115[8],plVar115 + 0x1b);
/* 61d8*/          ppppppplVar46 = ppppppplStack_2c0;
/* 61d8*/          ppppppplVar122 = ppppppplStack_2c8;
/* 61f8*/          ppppppplStack_6e0 = ppppppplStack_2c8;
/* 61f8*/          ppppppplStack_6c8 = ppppppplStack_2c0;
/* 61f8*/          if (ppppppplStack_2d0 != (longlong *******)0x2) {
/* 6208*/            ppppppplStack_520 = ppppppplStack_2a8;
/* 6218*/            ppppppplStack_528 = ppppppplStack_2b0;
/* 6228*/            ppppppplStack_530 = ppppppplStack_2b8;
/* 6230*/            if (ppppppplStack_2d0 != (longlong *******)0x1) goto joined_r0x00029278;
/* 6250*/            solana_sysvar::clock::<impl_solana_sysvar::Sysvar_for_solana_clock::Clock>::get
/* 6248*/                      (&ppppppplStack_2d0);
/* 6250*/            ppppppplVar112 = ppppppplStack_2c0;
/* 6250*/            ppppppplVar97 = ppppppplStack_2c8;
/* 6260*/            if (ppppppplStack_2d0 == (longlong *******)0x0) {
/* 63c8*/              puVar48 = (undefined8 *)plVar115[0x15];
/* 63d0*/              uStack_438 = puVar48[3];
/* 63e0*/              ppppppplStack_440 = (longlong *******)puVar48[2];
/* 63f0*/              ppppppplStack_448 = (longlong *******)puVar48[1];
/* 6400*/              uStack_450 = (char *)*puVar48;
/* 6410*/              ppppppplStack_408 = ppppppplVar122;
/* 6418*/              ppppppplStack_410 = ppppppplStack_2a8;
/* 6420*/              ppppppplStack_430 = ppppppplVar46;
/* 6430*/              ppppppplStack_428 = ppppppplStack_530;
/* 6440*/              ppppppplStack_420 = ppppppplStack_528;
/* 6450*/              ppppppplStack_418 = ppppppplStack_520;
/* 6480*/              <pump_recovered::creator::collect_creator_fee::CollectCreatorFeeEvent_as_anchor_lang::Event>::data
/* 6460*/                        (&ppppppplStack_2d0,&uStack_450);
/* 6490*/              ppppppplStack_30 = ppppppplStack_2c0;
/* 64a0*/              uStack_38 = (char *)ppppppplStack_2c8;
/* 64b0*/              solana_program::log::sol_log_data(&uStack_38,1);
/* 64f0*/              <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 64d0*/                        (&ppppppplStack_518,plVar115 + 0x27);
/* 6500*/              uVar5 = *(undefined1 *)(param_2 + 0x2e);
/* 6528*/              <pump_recovered::creator::collect_creator_fee::CollectCreatorFeeEvent_as_anchor_lang::Event>::data
/* 6470*/                        (&ppppppplStack_4e8,&uStack_450);
/* 6558*/              puStack_490 = &DAT_1b64c7_1b64c7;
/* 6560*/              ppppppplStack_498 = (longlong *******)&DAT_1b64bf_1b64bf;
/* 6570*/              uStack_4a8 = SUB87(ppppppplStack_4e8,0);
/* 6570*/              uStack_4a1 = (undefined1)((ulonglong)ppppppplStack_4e8 >> 0x38);
/* 6580*/              uStack_4b0 = SUB87(ppppppplStack_4e0,0);
/* 6580*/              uStack_4a9 = (undefined1)((ulonglong)ppppppplStack_4e0 >> 0x38);
/* 6588*/              uStack_4b8._0_4_ = SUB84(ppppppplStack_4e0,0);
/* 6588*/              uStack_4b8._4_1_ = (undefined1)((ulonglong)ppppppplStack_4e0 >> 0x20);
/* 6588*/              uStack_4b8._5_2_ = (undefined2)((ulonglong)ppppppplStack_4e0 >> 0x28);
/* 65a0*/              uStack_4a0 = SUB87((undefined *)
/* 6598*/                                 ((longlong)ppppppplStack_4e0 + (longlong)ppppppplStack_4d8),0);
/* 65a0*/              bStack_499 = (byte)((ulonglong)
/* 6598*/                                  ((longlong)ppppppplStack_4e0 + (longlong)ppppppplStack_4d8) >>
/* 65a0*/                                 0x38);
/* 65c8*/              uStack_4b8._7_1_ = uStack_4a9;
/* 65c8*/              <alloc::vec::Vec<T>_as_alloc::vec::spec_from_iter::SpecFromIter<T,I>>::from_iter
/* 65b0*/                        (&pppppplStack_4d0,&uStack_4b8);
/* 65c8*/              uVar98 = uStack_4c8;
/* 65f8*/              ppppppplStack_30 = (longlong *******)alloc::alloc::exchange_malloc(0x22,1);
/* 6608*/              pppppplVar74 = ppppppplStack_518[3];
/* 6610*/              pppppplVar73 = ppppppplStack_518[2];
/* 6618*/              pppppplVar91 = ppppppplStack_518[1];
/* 6620*/              *ppppppplStack_30 = *ppppppplStack_518;
/* 6630*/              ppppppplStack_30[1] = pppppplVar91;
/* 6638*/              ppppppplStack_30[2] = pppppplVar73;
/* 6640*/              ppppppplStack_30[3] = pppppplVar74;
/* 6648*/              *(undefined2 *)(ppppppplStack_30 + 4) = 1;
/* 6658*/              uStack_38 = (char *)0x1;
/* 6660*/              ppppppplStack_28 = (longlong *******)0x1;
/* 66b0*/              solana_instruction::Instruction::new_with_bytes
/* 6670*/                        (&ppppppplStack_2d0,PUMP_PROGRAM_ID_1b79df,uVar98,uStack_4c0,&uStack_38);
/* 64e0*/              memcpy(&uStack_38,&ppppppplStack_518,0x30);
/* 66f0*/              ppppppplStack_680 = (longlong *******)&ppppppplStack_470;
/* 6708*/              ppppppplStack_460 = (longlong *******)&ppppppplStack_548;
/* 6728*/              ppppppplStack_470 = (longlong *******)0x1b6807;
/* 6738*/              ppppppplStack_548 = (longlong *******)CONCAT71(ppppppplStack_548._1_7_,uVar5);
/* 6740*/              ppppppplStack_678 = (longlong *******)0x2;
/* 6748*/              uStack_458 = 1;
/* 6750*/              ppppppplStack_468 = (longlong *******)0x11;
/* 6670*/              solana_program::program::invoke_signed(&uStack_488,&ppppppplStack_2d0,&uStack_38,1);
/* 67c8*/              if (uStack_488 == (longlong *******)0x800000000000001a) {
/* 67e8*/                pppppplVar74 = *ppppppplStack_30;
/* 67f0*/                *ppppppplStack_30 = (longlong ******)((longlong)pppppplVar74 + -1);
/* 67f0*/                if ((longlong ******)((longlong)pppppplVar74 + -1) == (longlong ******)0x0) {
/* 6808*/                  ppppppplStack_30[1] = (longlong ******)((longlong)ppppppplStack_30[1] + -1);
/* 6820*/                pppppplVar74 = *ppppppplStack_28;
/* 6828*/                *ppppppplStack_28 = (longlong ******)((longlong)pppppplVar74 + -1);
/* 6828*/                if ((longlong ******)((longlong)pppppplVar74 + -1) == (longlong ******)0x0) {
/* 6840*/                  ppppppplStack_28[1] = (longlong ******)((longlong)ppppppplStack_28[1] + -1);
/* 6868*/                goto joined_r0x00029278;
/* 6a68*/              <anchor_lang::error::Error_as_core::convert::From<solana_program_error::ProgramError>>::from
/* 6a50*/                        (&ppppppplStack_790,&uStack_488);
/* 6a90*/              pppppplVar74 = *ppppppplStack_30;
/* 6a98*/              *ppppppplStack_30 = (longlong ******)((longlong)pppppplVar74 + -1);
/* 6a98*/              if ((longlong ******)((longlong)pppppplVar74 + -1) == (longlong ******)0x0) {
/* 6ab0*/                ppppppplStack_30[1] = (longlong ******)((longlong)ppppppplStack_30[1] + -1);
/* 6ac8*/              pppppplVar74 = *ppppppplStack_28;
/* 6ad0*/              *ppppppplStack_28 = (longlong ******)((longlong)pppppplVar74 + -1);
/* 6ae0*/              ppppppplStack_6e0 = ppppppplStack_790;
/* 6ae0*/              ppppppplStack_6c8 = ppppppplStack_788;
/* 6ad0*/              if ((longlong ******)((longlong)pppppplVar74 + -1) == (longlong ******)0x0) {
/* 6ae8*/                ppppppplStack_28[1] = (longlong ******)((longlong)ppppppplStack_28[1] + -1);
/* 6280*/              ppppppplStack_2c0 = ppppppplStack_2b8;
/* 6288*/              ppppppplStack_2c8 = ppppppplVar112;
/* 6290*/              ppppppplStack_2d0 = ppppppplVar97;
/* 62b8*/              <anchor_lang::error::Error_as_core::convert::From<solana_program_error::ProgramError>>::from
/* 62a0*/                        (&ppppppplStack_780,&ppppppplStack_2d0);
/* 62c8*/              ppppppplStack_6e0 = ppppppplStack_780;
/* 62c8*/              ppppppplStack_6c8 = ppppppplStack_778;
/* 5c20*/          lVar103 = solana_account_info::AccountInfo::data_is_empty(plVar115[9]);
/* 5c30*/          bVar101 = false;
/* 5c38*/          bVar102 = false;
/* 5c40*/          if (lVar103 == 0) {
/* 6308*/            pump_recovered::admin_cto::token_frozen(&ppppppplStack_2d0,plVar115[9]);
/* 6330*/            ppppppplStack_6e0 = ppppppplStack_2d0;
/* 6330*/            ppppppplStack_6c8 = ppppppplStack_2c8;
/* 6338*/            bVar102 = true;
/* 6348*/            if ((byte)ppppppplStack_2c8 != '\0') {
/* 6350*/              bVar102 = false;
/* 5c58*/          if (lVar120 == 0) {
/* 5c60*/LAB_ram_00028670:
/* 5c68*/            pump_recovered::admin_cto::token_frozen(&ppppppplStack_2d0,plVar115[0x11]);
/* 5c90*/            ppppppplStack_6e0 = ppppppplStack_2d0;
/* 5c90*/            ppppppplStack_6c8 = ppppppplStack_2c8;
/* 5ca0*/            bVar101 = true;
/* 5cb0*/            if ((byte)ppppppplStack_2c8 != '\0') {
/* 5cb8*/              bVar101 = false;
/* 5ce0*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5cc8*/                    (&ppppppplStack_2b8,plVar115[5]);
/* 5ce8*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(&uStack_450,*plVar115);
/* 5d28*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5d10*/                    (&ppppppplStack_420,plVar115[8]);
/* 5d38*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_3f0,plVar81);
/* 5d70*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5d50*/                    (auStack_3c0,*(undefined8 *)(plVar115[3] + 0x58));
/* 5d78*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_390,plVar115[6]);
/* 5d98*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_360,plVar115[4]);
/* 5cf8*/          memcpy(&ppppppplStack_288,&uStack_450,0x120);
/* 5de0*/          plStack_160 = (longlong *)0x0;
/* 5de8*/          uStack_168 = 8;
/* 5df0*/          ppppppplStack_2c0 = (longlong *******)0x0;
/* 5df8*/          ppppppplStack_2c8 = (longlong *******)0x8;
/* 5e00*/          ppppppplStack_2d0 = (longlong *******)0x0;
/* 5e10*/          anchor_spl::associated_token::create_idempotent(&ppppppplStack_770,&ppppppplStack_2d0);
/* 5e38*/          ppppppplStack_6e0 = ppppppplStack_770;
/* 5e38*/          ppppppplStack_6c8 = ppppppplStack_768;
/* 5e48*/          if (bVar102) goto LAB_ram_00028b30;
/* 6868*/joined_r0x00029278:
/* 6898*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 6880*/                    (&ppppppplStack_2b8,plVar115[0xb]);
/* 68c8*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 68a0*/                    (&uStack_450,*(undefined8 *)(plVar115[3] + 0x58));
/* 68e8*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 68d0*/                    (&ppppppplStack_420,plVar115[4]);
/* 68f8*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_3f0,plVar81);
/* 6928*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 6910*/                    (auStack_3c0,plVar115[0x10]);
/* 6948*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 6930*/                    (auStack_390,plVar115[0x11]);
/* 6950*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_360,plVar115[8]);
/* 6970*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_330,plVar115[0xf])
/* 6990*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_300,plVar115[0xb])
/* 68b8*/          memcpy(&ppppppplStack_288,&uStack_450,0x180);
/* 69d8*/          plStack_100 = (longlong *)0x0;
/* 69e0*/          lStack_108 = 8;
/* 69e8*/          ppppppplStack_2c0 = (longlong *******)0x0;
/* 69f0*/          ppppppplStack_2c8 = (longlong *******)0x8;
/* 69f8*/          ppppppplStack_2d0 = (longlong *******)0x0;
/* 6a20*/          pump_recovered::pump_amm::cpi::collect_coin_creator_fee
/* 6a08*/                    (&ppppppplStack_7a0,&ppppppplStack_2d0);
/* 6a30*/          ppppppplStack_6e0 = ppppppplStack_7a0;
/* 6a30*/          ppppppplStack_6c8 = ppppppplStack_798;
/* 6398*/joined_r0x00028da8:
/* 5e78*/              ppppppplStack_6e0 = (longlong *******)0x2;
/* 5e70*/              ppppppplStack_7d8 = (longlong *******)0x0;
/* 5e88*/              if (ppppppplVar122 != (longlong *******)0x0) {
/* 5eb0*/                <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5e98*/                          (&ppppppplStack_2b8,plVar115[5]);
/* 5ed8*/                <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5eb8*/                          (&uStack_450,*plVar115);
/* 5ef8*/                <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5ee0*/                          (&ppppppplStack_420,plVar115[10]);
/* 5f08*/                <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_3f0,plVar81)
/* 5f40*/                <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5f20*/                          (auStack_3c0,*(undefined8 *)(plVar115[3] + 0x58));
/* 5f60*/                <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5f48*/                          (auStack_390,plVar115[6]);
/* 5f80*/                <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5f68*/                          (auStack_360,plVar115[4]);
/* 5ec8*/                memcpy(&ppppppplStack_288,&uStack_450,0x120);
/* 5fb0*/                plStack_160 = (longlong *)0x0;
/* 5fb8*/                uStack_168 = 8;
/* 5fc0*/                ppppppplStack_2c0 = (longlong *******)0x0;
/* 5fc8*/                ppppppplStack_2c8 = (longlong *******)0x8;
/* 5fd0*/                ppppppplStack_2d0 = (longlong *******)0x0;
/* 5ff8*/                anchor_spl::associated_token::create_idempotent
/* 5fe0*/                          (&ppppppplStack_810,&ppppppplStack_2d0);
/* 6008*/                ppppppplStack_6e0 = ppppppplStack_810;
/* 6008*/                ppppppplStack_7d8 = ppppppplStack_808;
/* 6008*/                if (ppppppplStack_810 == (longlong *******)0x2) {
/* 60b8*/                  pump_recovered::payments::collect_transfer_vault_tokens
/* 60c8*/                  ppppppplStack_6e0 = ppppppplStack_820;
/* 60c8*/                  ppppppplStack_7d8 = ppppppplStack_818;
