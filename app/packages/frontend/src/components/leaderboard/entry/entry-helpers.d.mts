import type { Entry } from "./original-entry-row";
export const squadVariants: ReadonlyArray<{
  sha256: string;
  path: string;
  source: string;
}>;
export const imageVariants: ReadonlyArray<{
  sha256: string;
  path: string;
  source: string;
}>;
export function createEntryHelpers(capabilities: {
  squadVariant: string;
  imageVariant: string;
  Intl: typeof Intl;
}): {
  profileHref: (value: string) => string | null;
  shortWallet: (value: string) => string;
  isVerified: (value: Entry) => boolean;
  formatPnl: (value: number) => string;
  squadHref: (value: { groupId: string; username: string | null }) => string;
  normalizeImage: (value: string | null) => string | undefined;
  ipfsPrefix: string;
};
