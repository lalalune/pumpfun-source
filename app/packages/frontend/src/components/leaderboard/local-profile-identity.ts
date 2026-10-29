import { isValidProfileIdentifier } from "../profile/profile-identifier";

/** A hash-bound synthetic display/link hint, never ownership or authorization. */
export type LocalRankingProfile = {
  walletAddress: string;
  userId: string | null;
  username: string | null;
};

export function matchingLocalRankingProfile(
  row: LocalRankingProfile,
  available: readonly LocalRankingProfile[],
): string | null {
  if (!isValidProfileIdentifier(row.walletAddress)) return null;
  return available.some(
    (profile) =>
      profile.walletAddress === row.walletAddress &&
      profile.userId === row.userId &&
      profile.username === row.username,
  )
    ? row.walletAddress
    : null;
}
