/** Presentation only. This interface cannot connect, authenticate, sign, or store credentials. */
export type WalletPresentation = Readonly<{
  name: string;
  readiness: "unavailable" | "installed" | "loadable";
}>;

export type AuthPresentation = Readonly<{
  source: "unavailable" | "synthetic-test";
  session: "unavailable" | "anonymous" | "expired";
  wallets: readonly WalletPresentation[];
  recentWallet: string | null;
}>;

export interface AuthPresentationAdapter {
  read(signal: AbortSignal): Promise<unknown>;
}

export const AUTH_OPEN_TIMEOUT_MS = 15_000;

const unavailablePresentation: AuthPresentation = Object.freeze({
  source: "unavailable",
  session: "unavailable",
  // Named in factory 180013. This is a catalogue, never extension detection.
  wallets: Object.freeze([
    Object.freeze({ name: "Phantom", readiness: "unavailable" }),
    Object.freeze({ name: "Coinbase Wallet", readiness: "unavailable" }),
    Object.freeze({ name: "Magic Eden", readiness: "unavailable" }),
  ]),
  recentWallet: null,
});

export const unavailableAuthAdapter: AuthPresentationAdapter = Object.freeze({
  async read(signal: AbortSignal): Promise<AuthPresentation> {
    signal.throwIfAborted();
    return unavailablePresentation;
  },
});

function record(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

/** Reject unsupported session claims, provider URLs and accidental live-wallet flags. */
export function parseAuthPresentation(
  value: unknown,
  allowSynthetic = false,
): AuthPresentation {
  if (!record(value)) throw new Error("Invalid auth presentation");
  const source = value.source;
  if (
    source !== "unavailable" &&
    !(allowSynthetic && source === "synthetic-test")
  ) {
    throw new Error("Unsupported auth presentation source");
  }
  const session = value.session;
  if (
    session !== "unavailable" &&
    session !== "anonymous" &&
    session !== "expired"
  ) {
    throw new Error("Unsupported session presentation");
  }
  if (!Array.isArray(value.wallets) || value.wallets.length > 100) {
    throw new Error("Invalid wallet presentation");
  }
  const names = new Set<string>();
  const wallets = Array.from(value.wallets, (wallet): WalletPresentation => {
    if (
      !record(wallet) ||
      typeof wallet.name !== "string" ||
      wallet.name.length < 1 ||
      wallet.name.length > 80 ||
      wallet.name.trim() !== wallet.name ||
      /[\u0000-\u001f\u007f]/u.test(wallet.name) ||
      names.has(wallet.name) ||
      (wallet.readiness !== "unavailable" &&
        wallet.readiness !== "installed" &&
        wallet.readiness !== "loadable")
    ) {
      throw new Error("Invalid wallet presentation");
    }
    names.add(wallet.name);
    if (source === "unavailable" && wallet.readiness !== "unavailable") {
      throw new Error("Unavailable adapter cannot claim detected wallets");
    }
    return Object.freeze({
      name: wallet.name,
      readiness: wallet.readiness,
    });
  });
  const recentWallet = value.recentWallet;
  if (
    recentWallet !== null &&
    (typeof recentWallet !== "string" || !names.has(recentWallet))
  ) {
    throw new Error("Invalid recent wallet presentation");
  }
  if (
    source === "unavailable" &&
    (session !== "unavailable" || recentWallet !== null)
  ) {
    throw new Error(
      "Unavailable adapter cannot claim a session or remembered wallet",
    );
  }
  return Object.freeze({
    source,
    session,
    wallets: Object.freeze(wallets),
    recentWallet,
  });
}

/** Captured 180013: recent > installed > others; two preview choices, then named fallbacks. */
export function walletChoices(
  presentation: AuthPresentation,
  expanded: boolean,
) {
  const { wallets, recentWallet } = presentation;
  const score = (wallet: WalletPresentation) =>
    (wallet.name === recentWallet ? 2 : 0) +
    (wallet.readiness === "installed" ? 1 : 0);
  const sorted = [...wallets].sort((left, right) => score(right) - score(left));
  if (expanded) return sorted;
  const selected = new Set<string>();
  const select = (wallet: WalletPresentation | undefined) => {
    if (wallet && selected.size < 2) selected.add(wallet.name);
  };
  sorted
    .filter(
      (wallet) =>
        wallet.readiness === "installed" || wallet.name === recentWallet,
    )
    .forEach(select);
  for (const name of ["Phantom", "Coinbase Wallet"])
    select(wallets.find((wallet) => wallet.name === name));
  return sorted.filter((wallet) => selected.has(wallet.name));
}
