import type {
  StoredWalletRecord,
  WalletRecordSuccess,
} from "../wallet-program-record/types";

/** Published AMM IDL has no stable-cashback fields. Missing fields stay absent. */
export type StoredAmmWalletRecord = Pick<
  StoredWalletRecord,
  | "user"
  | "needsClaim"
  | "hasTotalClaimedTokens"
  | "totalUnclaimedTokens"
  | "totalClaimedTokens"
  | "currentSolVolume"
  | "lastUpdateTimestamp"
  | "cashbackEarned"
  | "totalCashbackClaimed"
>;
export type AmmWalletRecordSuccess = Omit<WalletRecordSuccess, "record"> & {
  record: StoredAmmWalletRecord | null;
};
