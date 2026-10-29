// Explicit synthetic host values, not an upstream response or computed ranking.
export const wallet = "11111111111111111111111111111112";
const template = {
  entryId: "",
  participantId: "",
  kind: "person",
  rank: 0,
  pnlUsd: 0,
  realizedPnlUsd: 0,
  unrealizedPnlUsd: 0,
  buySpendSol: 0,
  memberCount: 0,
  membersFresh: 0,
  struck: false,
  lastRefreshedAtMs: 0,
  positionsCount: 0,
  topPositions: [],
  walletAddress: null,
  username: null,
  profileImageUrl: null,
  isVerified: false,
  verifiedBadgeVisible: false,
};
export const rows = [
  {
    entry: {
      ...template,
      entryId: "person",
      participantId: "person-fixture",
      rank: 1,
      pnlUsd: 1000,
      walletAddress: wallet,
      username: "FixtureTrader",
      profileImageUrl: "  https://fixture.invalid/avatar.png  ",
      isVerified: true,
      verifiedBadgeVisible: true,
    },
    prize: { rankFrom: 1, rankTo: 1, amount: "1000" },
  },
  {
    entry: {
      ...template,
      entryId: "group",
      participantId: "group/fixture",
      kind: "group",
      rank: 2,
      pnlUsd: -25,
      memberCount: 3,
      username: "create",
      isVerified: true,
      verifiedBadgeVisible: false,
    },
    prize: null,
  },
  {
    entry: {
      ...template,
      entryId: "anonymous",
      participantId: "anonymous-fixture",
      rank: 3,
      pnlUsd: 0,
      username: null,
    },
    prize: { rankFrom: 3, rankTo: 5, amount: "2 SOL" },
  },
  {
    entry: {
      ...template,
      entryId: "unranked",
      participantId: "unranked-fixture",
      username: "",
    },
    prize: null,
  },
];
export function syntheticTranslate(key, values = {}) {
  switch (key) {
    case "web.leaderboard.squads_unnamed_row":
      return "fixture-unnamed-squad";
    case "web.leaderboard.cup.anonymous":
      return "fixture-anonymous";
    case "profile.squads.info.member_count":
      return "fixture-members:" + values.count;
    default:
      throw Error("Unobserved fixture translation key");
  }
}
