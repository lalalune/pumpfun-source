import { isObservationInstant } from "../../lib/observation-time.mjs";
export const MAINNET_GENESIS_HASH =
  "5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d";
export const SPL_TOKEN_PROGRAM_ID =
  "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";
export const TOKEN_2022_PROGRAM_ID =
  "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb";

export type TokenProgram = "spl-token" | "token-2022";

export type PortfolioTokenAccount = {
  tokenAccount: string;
  mint: string;
  owner: string;
  program: TokenProgram;
  programId: string;
  rawAmount: string;
  decimals: number;
  amount: string;
  state: "uninitialized" | "initialized" | "frozen";
  isNative: boolean;
  extensions: string[];
};

export type PortfolioMintHolding = {
  mint: string;
  program: TokenProgram;
  programId: string;
  rawAmount: string;
  decimals: number;
  amount: string;
  accountCount: number;
};

export type PortfolioProgramHoldings = {
  program: TokenProgram;
  programId: string;
  contextSlot: number;
  accounts: PortfolioTokenAccount[];
  mints: PortfolioMintHolding[];
};

export type PortfolioSuccess = {
  ok: true;
  address: string;
  cluster: "mainnet-beta";
  genesisHash: string;
  commitment: "confirmed";
  observedAt: string;
  endpointHost: string;
  sol: {
    lamports: string;
    amount: string;
    contextSlot: number;
  };
  splToken: PortfolioProgramHoldings;
  token2022: PortfolioProgramHoldings;
  snapshotAtomic: false;
};

export type PortfolioFailure = {
  ok: false;
  error: {
    code: string;
    message: string;
    retryable: boolean;
  };
};

export type PortfolioResponse = PortfolioSuccess | PortfolioFailure;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function hasAmount(raw: unknown, decimals: unknown, amount: unknown): boolean {
  if (
    typeof raw !== "string" ||
    raw.length > 20 ||
    !/^(0|[1-9]\d*)$/.test(raw) ||
    BigInt(raw) > 18_446_744_073_709_551_615n
  )
    return false;
  if (
    typeof decimals !== "number" ||
    !Number.isInteger(decimals) ||
    decimals < 0 ||
    decimals > 255
  )
    return false;
  const padded = raw.padStart(decimals + 1, "0");
  return (
    amount ===
    (decimals === 0
      ? raw
      : `${padded.slice(0, -decimals)}.${padded.slice(-decimals)}`)
  );
}

function isTokenAccount(value: unknown): value is PortfolioTokenAccount {
  return (
    isRecord(value) &&
    typeof value.tokenAccount === "string" &&
    typeof value.mint === "string" &&
    typeof value.owner === "string" &&
    (value.program === "spl-token" || value.program === "token-2022") &&
    typeof value.programId === "string" &&
    hasAmount(value.rawAmount, value.decimals, value.amount) &&
    typeof value.state === "string" &&
    ["uninitialized", "initialized", "frozen"].includes(value.state) &&
    typeof value.isNative === "boolean" &&
    Array.isArray(value.extensions) &&
    value.extensions.every((extension) => typeof extension === "string")
  );
}

function isMintHolding(value: unknown): value is PortfolioMintHolding {
  return (
    isRecord(value) &&
    typeof value.mint === "string" &&
    (value.program === "spl-token" || value.program === "token-2022") &&
    typeof value.programId === "string" &&
    hasAmount(value.rawAmount, value.decimals, value.amount) &&
    Number.isSafeInteger(value.accountCount) &&
    Number(value.accountCount) > 0
  );
}

function isProgramHoldings(
  value: unknown,
  expected: TokenProgram,
): value is PortfolioProgramHoldings {
  return (
    isRecord(value) &&
    value.program === expected &&
    value.programId ===
      (expected === "spl-token"
        ? SPL_TOKEN_PROGRAM_ID
        : TOKEN_2022_PROGRAM_ID) &&
    Number.isSafeInteger(value.contextSlot) &&
    Number(value.contextSlot) >= 0 &&
    Array.isArray(value.accounts) &&
    value.accounts.every(
      (account) =>
        isTokenAccount(account) &&
        account.program === expected &&
        account.programId === value.programId,
    ) &&
    Array.isArray(value.mints) &&
    value.mints.every(
      (mint) =>
        isMintHolding(mint) &&
        mint.program === expected &&
        mint.programId === value.programId,
    )
  );
}

export function isPortfolioResponse(
  value: unknown,
  expectedAddress?: string,
): value is PortfolioResponse {
  if (!isRecord(value) || typeof value.ok !== "boolean") return false;
  if (value.ok === false) {
    return (
      isRecord(value.error) &&
      typeof value.error.code === "string" &&
      typeof value.error.message === "string" &&
      typeof value.error.retryable === "boolean"
    );
  }
  return (
    typeof value.address === "string" &&
    (expectedAddress === undefined || value.address === expectedAddress) &&
    value.cluster === "mainnet-beta" &&
    value.genesisHash === MAINNET_GENESIS_HASH &&
    value.commitment === "confirmed" &&
    isObservationInstant(value.observedAt) &&
    typeof value.endpointHost === "string" &&
    isRecord(value.sol) &&
    hasAmount(value.sol.lamports, 9, value.sol.amount) &&
    Number.isSafeInteger(value.sol.contextSlot) &&
    Number(value.sol.contextSlot) >= 0 &&
    isProgramHoldings(value.splToken, "spl-token") &&
    isProgramHoldings(value.token2022, "token-2022") &&
    (expectedAddress === undefined ||
      [...value.splToken.accounts, ...value.token2022.accounts].every(
        (account) => account?.owner === expectedAddress,
      )) &&
    value.snapshotAtomic === false
  );
}
