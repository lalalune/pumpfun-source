/* 6390*/          goto joined_r0x00028da0;
/* 60f0*/          bVar97 = true;
/* 6100*/          uStack_928 = 0;
/* 6110*/          if (uVar99 == 0) {
/* 5c50*/LAB_ram_00028660:
/* 5c58*/            pump_recovered::admin_cto::token_frozen(&ppppppplStack_2d0,puVar110[0x11]);
/* 5c80*/            ppppppplStack_6f0 = ppppppplStack_2d0;
/* 5c80*/            ppppppplStack_6e8 = ppppppplStack_2c8;
/* 5c98*/            uStack_928 = 1;
/* 5ca8*/            if ((char)ppppppplStack_2c8 != '\0') {
/* 5cb8*/              uStack_928 = 0;
/* 5cc0*/            goto LAB_ram_000286d0;
/* 6120*/LAB_ram_00028b30:
/* 61d8*/          pump_recovered::creator::collect_creator_fee::collect
/* 6150*/                    (&ppppppplStack_2d0,puVar45,puVar110[8],puVar110 + 0x1b);
/* 61d8*/          ppppppplVar83 = ppppppplStack_2c0;
/* 61d8*/          ppppppplVar69 = ppppppplStack_2c8;
/* 61f8*/          ppppppplStack_6f0 = ppppppplStack_2c8;
/* 61f8*/          ppppppplStack_7a8 = ppppppplStack_2c0;
/* 61f8*/          if (ppppppplStack_2d0 != (longlong *******)0x2) {
/* 6208*/            ppppppplStack_520 = ppppppplStack_2a8;
/* 6218*/            ppppppplStack_528 = ppppppplStack_2b0;
/* 6228*/            ppppppplStack_530 = ppppppplStack_2b8;
/* 6230*/            if (ppppppplStack_2d0 != (longlong *******)0x1) goto LAB_ram_00029250;
/* 6250*/            solana_sysvar::clock::<impl_solana_sysvar::Sysvar_for_solana_clock::Clock>::get
/* 6248*/                      (&ppppppplStack_2d0);
/* 6250*/            ppppppplVar109 = ppppppplStack_2c0;
/* 6250*/            ppppppplVar102 = ppppppplStack_2c8;
/* 6260*/            if (ppppppplStack_2d0 == (longlong *******)0x0) {
/* 63b0*/              puVar91 = (undefined8 *)puVar110[0x15];
/* 63b8*/              uStack_438 = puVar91[3];
/* 63c8*/              ppppppplStack_440 = (longlong *******)puVar91[2];
/* 63d8*/              ppppppplStack_448 = (longlong *******)puVar91[1];
/* 63e8*/              uStack_450 = (char *)*puVar91;
/* 63f8*/              ppppppplStack_408 = ppppppplVar69;
/* 6400*/              ppppppplStack_410 = ppppppplStack_2a8;
/* 6408*/              ppppppplStack_430 = ppppppplVar83;
/* 6418*/              ppppppplStack_428 = ppppppplStack_530;
/* 6428*/              ppppppplStack_420 = ppppppplStack_528;
/* 6438*/              ppppppplStack_418 = ppppppplStack_520;
/* 6468*/              <pump_recovered::creator::collect_creator_fee::CollectCreatorFeeEvent_as_anchor_lang::Event>::data
/* 6448*/                        (&ppppppplStack_2d0,&uStack_450);
/* 6478*/              ppppppplStack_30 = ppppppplStack_2c0;
/* 6488*/              uStack_38 = (char *)ppppppplStack_2c8;
/* 6498*/              solana_program::log::sol_log_data(&uStack_38,1);
/* 64d8*/              <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 64b8*/                        (&ppppppplStack_518,puVar110 + 0x27);
/* 64e8*/              uVar98 = *(undefined1 *)(param_2 + 0x2e);
/* 6510*/              <pump_recovered::creator::collect_creator_fee::CollectCreatorFeeEvent_as_anchor_lang::Event>::data
/* 6458*/                        (&ppppppplStack_4e8,&uStack_450);
/* 6540*/              puStack_490 = &DAT_1b64c7_1b64c7;
/* 6548*/              ppppppplStack_498 = (longlong *******)&DAT_1b64bf_1b64bf;
/* 6558*/              ppppppplStack_4a8 = ppppppplStack_4e8;
/* 6560*/              uStack_4b8 = (char *)CONCAT71(uStack_4df,cStack_4e0);
/* 6580*/              pcStack_4a0 = (char *)((longlong)uStack_4b8 + lStack_4d8);
/* 65b0*/              pppppplStack_4b0 = (longlong ******)uStack_4b8;
/* 65b0*/              <alloc::vec::Vec<T>_as_alloc::vec::spec_from_iter::SpecFromIter<T,I>>::from_iter
/* 6598*/                        (&puStack_4d0,&uStack_4b8);
/* 65b0*/              uVar59 = uStack_4c8;
/* 65e0*/              ppppppplStack_30 = (longlong *******)alloc::alloc::exchange_malloc(0x22,1);
/* 65f0*/              pppppplVar62 = ppppppplStack_518[3];
/* 65f8*/              pppppplVar118 = ppppppplStack_518[2];
/* 6600*/              pppppplVar92 = ppppppplStack_518[1];
/* 6608*/              *ppppppplStack_30 = *ppppppplStack_518;
/* 6618*/              ppppppplStack_30[1] = pppppplVar92;
/* 6620*/              ppppppplStack_30[2] = pppppplVar118;
/* 6628*/              ppppppplStack_30[3] = pppppplVar62;
/* 6630*/              *(undefined2 *)(ppppppplStack_30 + 4) = 1;
/* 6640*/              uStack_38 = (char *)0x1;
/* 6648*/              pppppplStack_28 = (longlong ******)0x1;
/* 6698*/              solana_instruction::Instruction::new_with_bytes
/* 6658*/                        (&ppppppplStack_2d0,PUMP_PROGRAM_ID_1b79df,uVar59,uStack_4c0,&uStack_38);
/* 64c8*/              memcpy(&uStack_38,&ppppppplStack_518,0x30);
/* 66d8*/              uStack_540 = (longlong *******)&ppppppplStack_470;
/* 66f0*/              ppppppplStack_460 = (longlong *******)&uStack_658;
/* 6710*/              ppppppplStack_470 = (longlong *******)0x1b6807;
/* 6728*/              uStack_538 = 2;
/* 6730*/              uStack_458 = 1;
/* 6738*/              ppppppplStack_468 = (longlong *******)0x11;
/* 6790*/              uStack_658 = uVar98;
/* 6658*/              solana_program::program::invoke_signed(&uStack_488,&ppppppplStack_2d0,&uStack_38,1);
/* 67b0*/              if (uStack_488 == (longlong *******)0x800000000000001a) {
/* 67d0*/                lVar106 = (longlong)*ppppppplStack_30;
/* 67d8*/                *ppppppplStack_30 = (longlong ******)(lVar106 + -1);
/* 67d8*/                if (lVar106 + -1 == 0) {
/* 67f0*/                  ppppppplStack_30[1] = (longlong ******)((longlong)ppppppplStack_30[1] + -1);
/* 6808*/                ppppplVar68 = *pppppplStack_28;
/* 6810*/                *pppppplStack_28 = (longlong *****)((longlong)ppppplVar68 + -1);
/* 6810*/                if ((longlong *****)((longlong)ppppplVar68 + -1) == (longlong *****)0x0) {
/* 6828*/                  pppppplStack_28[1] = (longlong *****)((longlong)pppppplStack_28[1] + -1);
/* 6840*/                goto LAB_ram_00029250;
/* 6a68*/              <anchor_lang::error::Error_as_core::convert::From<solana_program_error::ProgramError>>::from
/* 6a50*/                        (&ppppppplStack_790,&uStack_488);
/* 6a90*/              lVar106 = (longlong)*ppppppplStack_30;
/* 6a98*/              *ppppppplStack_30 = (longlong ******)(lVar106 + -1);
/* 6a98*/              if (lVar106 + -1 == 0) {
/* 6ab0*/                ppppppplStack_30[1] = (longlong ******)((longlong)ppppppplStack_30[1] + -1);
/* 6ac8*/              ppppplVar68 = *pppppplStack_28;
/* 6ad0*/              *pppppplStack_28 = (longlong *****)((longlong)ppppplVar68 + -1);
/* 6ae0*/              ppppppplStack_6f0 = ppppppplStack_790;
/* 6ae0*/              ppppppplStack_7a8 = ppppppplStack_788;
/* 6ad0*/              if ((longlong *****)((longlong)ppppplVar68 + -1) == (longlong *****)0x0) {
/* 6ae8*/                pppppplStack_28[1] = (longlong *****)((longlong)pppppplStack_28[1] + -1);
/* 6280*/              ppppppplStack_2c0 = ppppppplStack_2b8;
/* 6288*/              ppppppplStack_2c8 = ppppppplVar109;
/* 6290*/              ppppppplStack_2d0 = ppppppplVar102;
/* 62b8*/              <anchor_lang::error::Error_as_core::convert::From<solana_program_error::ProgramError>>::from
/* 62a0*/                        (&ppppppplStack_780,&ppppppplStack_2d0);
/* 62c8*/              ppppppplStack_6f0 = ppppppplStack_780;
/* 62c8*/              ppppppplStack_7a8 = ppppppplStack_778;
/* 5c08*/          lVar106 = solana_account_info::AccountInfo::data_is_empty(puVar110[9]);
/* 5c20*/          uStack_928 = 0;
/* 5c28*/          bVar97 = false;
/* 5c30*/          if (lVar106 == 0) {
/* 6310*/            pump_recovered::admin_cto::token_frozen(&ppppppplStack_2d0,puVar110[9]);
/* 6338*/            ppppppplStack_6f0 = ppppppplStack_2d0;
/* 6338*/            ppppppplStack_6e8 = ppppppplStack_2c8;
/* 6340*/            bVar97 = true;
/* 6350*/            if ((char)ppppppplStack_2c8 != '\0') {
/* 6358*/              bVar97 = false;
/* 5c48*/          if (uVar99 == 0) goto LAB_ram_00028660;
/* 5cc0*/LAB_ram_000286d0:
/* 5ce0*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5cc8*/                    (&ppppppplStack_2b8,puVar110[5]);
/* 5ce8*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(&uStack_450,*puVar110);
/* 5d28*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5d10*/                    (&ppppppplStack_420,puVar110[8]);
/* 5d38*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_3f0,puVar45);
/* 5d70*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5d50*/                    (auStack_3c0,*(undefined8 *)(puVar110[3] + 0x58));
/* 5d78*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_390,puVar110[6]);
/* 5d98*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_360,puVar110[4]);
/* 5cf8*/          memcpy(&ppppppplStack_288,&uStack_450,0x120);
/* 5de0*/          plStack_160 = (longlong *)0x0;
/* 5de8*/          uStack_168 = 8;
/* 5df0*/          ppppppplStack_2c0 = (longlong *******)0x0;
/* 5df8*/          ppppppplStack_2c8 = (longlong *******)0x8;
/* 5e00*/          ppppppplStack_2d0 = (longlong *******)0x0;
/* 5e10*/          anchor_spl::associated_token::create_idempotent(&ppppppplStack_770,&ppppppplStack_2d0);
/* 5e38*/          ppppppplStack_6f0 = ppppppplStack_770;
/* 5e38*/          ppppppplStack_6e8 = ppppppplStack_768;
/* 5e48*/          if (bVar97) goto LAB_ram_00028b30;
/* 6840*/LAB_ram_00029250:
/* 1d28*/          if ((uStack_928 & (uVar99 ^ 1)) == 0) goto LAB_ram_00024738;
/* 6898*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 6880*/                    (&ppppppplStack_2b8,puVar110[0xb]);
/* 68c8*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 68a0*/                    (&uStack_450,*(undefined8 *)(puVar110[3] + 0x58));
/* 68e8*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 68d0*/                    (&ppppppplStack_420,puVar110[4]);
/* 68f8*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_3f0,puVar45);
/* 6928*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 6910*/                    (auStack_3c0,puVar110[0x10]);
/* 6948*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 6930*/                    (auStack_390,puVar110[0x11]);
/* 6950*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_360,puVar110[8]);
/* 6970*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_330,puVar110[0xf])
/* 6990*/          <solana_account_info::AccountInfo_as_core::clone::Clone>::clone(auStack_300,puVar110[0xb])
/* 68b8*/          memcpy(&ppppppplStack_288,&uStack_450,0x180);
/* 69d8*/          plStack_100 = (longlong *)0x0;
/* 69e0*/          uStack_108 = 8;
/* 69e8*/          ppppppplStack_2c0 = (longlong *******)0x0;
/* 69f0*/          ppppppplStack_2c8 = (longlong *******)0x8;
/* 69f8*/          ppppppplStack_2d0 = (longlong *******)0x0;
/* 6a20*/          pump_recovered::pump_amm::cpi::collect_coin_creator_fee
/* 6a08*/                    (&ppppppplStack_7a0,&ppppppplStack_2d0);
/* 6a30*/          ppppppplStack_6f0 = ppppppplStack_7a0;
/* 6a30*/          ppppppplStack_7a8 = ppppppplStack_798;
/* 6390*/joined_r0x00028da0:
/* 6390*/        ppppppplStack_6e8 = ppppppplStack_7a8;
/* 1d28*/        goto LAB_ram_00024738;
/* 1d28*/LAB_ram_00024738:
/* 1d28*/  ppppppplVar69 = (longlong *******)0x0;
/* 1d30*/  if (bVar36) {
/* 5e58*/                ppppppplVar69 = (longlong *******)0x0;
/* 5e60*/                ppppppplStack_6f0 = (longlong *******)0x2;
/* 5e70*/                if (ppppppplStack_2c8 != (longlong *******)0x0) {
/* 5e98*/                  <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5e80*/                            (&ppppppplStack_2b8,puVar110[5]);
/* 5ec0*/                  <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5ea0*/                            (&uStack_450,*puVar110);
/* 5ee0*/                  <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5ec8*/                            (&ppppppplStack_420,puVar110[10]);
/* 5f00*/                  <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5ef0*/                            (auStack_3f0,puVar45);
/* 5f28*/                  <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5f08*/                            (auStack_3c0,*(undefined8 *)(puVar110[3] + 0x58));
/* 5f48*/                  <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5f30*/                            (auStack_390,puVar110[6]);
/* 5f68*/                  <solana_account_info::AccountInfo_as_core::clone::Clone>::clone
/* 5f50*/                            (auStack_360,puVar110[4]);
/* 5eb0*/                  memcpy(&ppppppplStack_288,&uStack_450,0x120);
/* 5f98*/                  plStack_160 = (longlong *)0x0;
/* 5fa0*/                  uStack_168 = 8;
/* 5fa8*/                  ppppppplStack_2c0 = (longlong *******)0x0;
/* 5fb0*/                  ppppppplStack_2c8 = (longlong *******)0x8;
/* 5fb8*/                  ppppppplStack_2d0 = (longlong *******)0x0;
/* 5fe0*/                  anchor_spl::associated_token::create_idempotent
/* 5fc8*/                            (&ppppppplStack_810,&ppppppplStack_2d0);
/* 5ff8*/                  if (ppppppplStack_810 == (longlong *******)0x2) {
/* 60a8*/                    pump_recovered::payments::collect_transfer_vault_tokens
/* 60b0*/                    ppppppplStack_6f0 = (longlong *******)0x2;
/* 60d0*/                    ppppppplStack_808 = ppppppplStack_818;
/* 60d0*/                    ppppppplStack_810 = ppppppplStack_820;
/* 60d0*/                    ppppppplVar69 = ppppppplVar83;
/* 60e8*/                  ppppppplVar69 = ppppppplStack_808;
/* 60e8*/                  ppppppplStack_6f0 = ppppppplStack_810;
