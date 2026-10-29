import { lookup } from "node:dns/promises";
import { request as httpsRequest } from "node:https";
import { isIP } from "node:net";
import { PublicKey } from "@solana/web3.js";
import {
  MAINNET_GENESIS_HASH,
  SPL_TOKEN_PROGRAM_ID,
  TOKEN_2022_PROGRAM_ID,
  type PortfolioMintHolding,
  type PortfolioProgramHoldings,
  type PortfolioSuccess,
  type PortfolioTokenAccount,
  type TokenProgram,
} from "./types";

export const DEFAULT_SOLANA_RPC_URL = "https://api.mainnet.solana.com";
export const RPC_COMMITMENT = "confirmed" as const;
const MAX_RPC_RESPONSE_BYTES = 16 * 1024 * 1024;
const MAX_TOKEN_ACCOUNTS = 20_000;
const MAX_U64 = 18_446_744_073_709_551_615n;

export type PortfolioErrorCode =
  | "INVALID_ADDRESS"
  | "RPC_CONFIGURATION_INVALID"
  | "RPC_DNS_REJECTED"
  | "RPC_RATE_LIMITED"
  | "RPC_TIMEOUT"
  | "RPC_UNAVAILABLE"
  | "RPC_RESPONSE_INVALID"
  | "WRONG_CLUSTER";

export class PortfolioRpcError extends Error {
  constructor(
    readonly code: PortfolioErrorCode,
    message: string,
    readonly retryable: boolean,
  ) {
    super(message);
    this.name = "PortfolioRpcError";
  }
}

type RpcMethod =
  | "getGenesisHash"
  | "getBalance"
  | "getTokenAccountsByOwner"
  | "getMultipleAccounts"
  | "getAccountInfo";
export type RpcCall = (
  method: RpcMethod,
  params: readonly unknown[],
  signal?: AbortSignal,
) => Promise<unknown>;

type PinnedEndpoint = {
  url: URL;
  hostname: string;
  address: string;
  family: 4 | 6;
};

type UnknownRecord = Record<string, unknown>;

function record(value: unknown, label: string): UnknownRecord {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new PortfolioRpcError(
      "RPC_RESPONSE_INVALID",
      `${label} must be an object.`,
      true,
    );
  }
  return value as UnknownRecord;
}

function text(value: unknown, label: string, maximum = 200): string {
  if (
    typeof value !== "string" ||
    value.length === 0 ||
    value.length > maximum
  ) {
    throw new PortfolioRpcError(
      "RPC_RESPONSE_INVALID",
      `${label} must be a bounded string.`,
      true,
    );
  }
  return value;
}

function safeInteger(value: unknown, label: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value < 0) {
    throw new PortfolioRpcError(
      "RPC_RESPONSE_INVALID",
      `${label} must be a non-negative safe integer.`,
      true,
    );
  }
  return value;
}

function boolean(value: unknown, label: string): boolean {
  if (typeof value !== "boolean") {
    throw new PortfolioRpcError(
      "RPC_RESPONSE_INVALID",
      `${label} must be a boolean.`,
      true,
    );
  }
  return value;
}

function publicKey(value: unknown, label: string): string {
  const address = text(value, label, 44);
  try {
    const canonical = new PublicKey(address).toBase58();
    if (canonical !== address) throw new Error("non-canonical");
  } catch {
    throw new PortfolioRpcError(
      "RPC_RESPONSE_INVALID",
      `${label} must be a canonical Solana public key.`,
      true,
    );
  }
  return address;
}

export function validateWalletAddress(value: string): string {
  const address = value.trim();
  try {
    const canonical = new PublicKey(address).toBase58();
    if (canonical !== address) throw new Error("non-canonical");
  } catch {
    throw new PortfolioRpcError(
      "INVALID_ADDRESS",
      "Enter a canonical Solana public-key address.",
      false,
    );
  }
  return address;
}

function u64(value: unknown, label: string): bigint {
  const raw =
    typeof value === "number" && Number.isSafeInteger(value)
      ? String(value)
      : value;
  if (typeof raw !== "string" || raw.length > 20 || !/^(0|[1-9]\d*)$/u.test(raw)) {
    throw new PortfolioRpcError(
      "RPC_RESPONSE_INVALID",
      `${label} must be an unsigned integer.`,
      true,
    );
  }
  const parsed = BigInt(raw);
  if (parsed > MAX_U64) {
    throw new PortfolioRpcError(
      "RPC_RESPONSE_INVALID",
      `${label} exceeds u64.`,
      true,
    );
  }
  return parsed;
}

export function formatBaseUnits(raw: bigint, decimals: number): string {
  if (!Number.isInteger(decimals) || decimals < 0 || decimals > 255) {
    throw new PortfolioRpcError(
      "RPC_RESPONSE_INVALID",
      "Token decimals are outside the supported range.",
      true,
    );
  }
  const digits = raw.toString();
  if (decimals === 0) return digits;
  const padded = digits.padStart(decimals + 1, "0");
  return `${padded.slice(0, -decimals)}.${padded.slice(-decimals)}`;
}

function isPrivateIpv4(address: string): boolean {
  const octets = address.split(".").map(Number);
  const [a, b, c] = octets;
  return (
    a === 0 ||
    a === 10 ||
    a === 127 ||
    (a === 100 && b >= 64 && b <= 127) ||
    (a === 169 && b === 254) ||
    (a === 172 && b >= 16 && b <= 31) ||
    (a === 192 && b === 0 && (c === 0 || c === 2)) ||
    (a === 192 && b === 168) ||
    (a === 198 && (b === 18 || b === 19)) ||
    (a === 198 && b === 51 && c === 100) ||
    (a === 203 && b === 0 && c === 113) ||
    a >= 224
  );
}

function isPrivateIp(address: string): boolean {
  if (isIP(address) === 4) return isPrivateIpv4(address);
  const normalized = address.toLowerCase();
  if (normalized.startsWith("::ffff:")) {
    return isPrivateIpv4(normalized.slice(7));
  }
  return (
    normalized === "::" ||
    normalized === "::1" ||
    normalized.startsWith("fc") ||
    normalized.startsWith("fd") ||
    normalized.startsWith("fe8") ||
    normalized.startsWith("fe9") ||
    normalized.startsWith("fea") ||
    normalized.startsWith("feb") ||
    normalized.startsWith("ff") ||
    normalized.startsWith("2001:db8:")
  );
}

export function isPublicRpcAddress(address: string): boolean {
  return isIP(address) !== 0 && !isPrivateIp(address);
}

export function validateRpcUrl(raw: string | undefined): URL {
  if (raw === undefined) {
    throw new PortfolioRpcError(
      "RPC_CONFIGURATION_INVALID",
      "SOLANA_RPC_URL is not configured; live portfolio reads are disabled.",
      false,
    );
  }
  const configured = raw.trim();
  if (!configured) {
    throw new PortfolioRpcError(
      "RPC_CONFIGURATION_INVALID",
      "SOLANA_RPC_URL is empty.",
      false,
    );
  }
  let url: URL;
  try {
    url = new URL(configured);
  } catch {
    throw new PortfolioRpcError(
      "RPC_CONFIGURATION_INVALID",
      "SOLANA_RPC_URL must be a valid HTTPS URL.",
      false,
    );
  }
  if (
    url.protocol !== "https:" ||
    url.username ||
    url.password ||
    url.hash ||
    (url.port && url.port !== "443") ||
    isIP(url.hostname) !== 0 ||
    url.hostname === "localhost" ||
    url.hostname.endsWith(".local")
  ) {
    throw new PortfolioRpcError(
      "RPC_CONFIGURATION_INVALID",
      "SOLANA_RPC_URL must use a public HTTPS hostname without credentials or fragments.",
      false,
    );
  }
  return url;
}

async function pinRpcEndpoint(
  raw: string | undefined,
  timeoutMs: number,
  signal?: AbortSignal,
): Promise<PinnedEndpoint> {
  const url = validateRpcUrl(raw);
  signal?.throwIfAborted();
  if (
    !Number.isSafeInteger(timeoutMs) ||
    timeoutMs < 0 ||
    timeoutMs > 2_147_483_647
  )
    throw new RangeError(
      "RPC timeout must be an integer from 0 to 2147483647 milliseconds",
    );
  let addresses: Array<{ address: string; family: number }>;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let onAbort: (() => void) | undefined;
  try {
    const interrupted = new Promise<never>((_resolve, reject) => {
      timer = setTimeout(() => reject(new PortfolioRpcError(
        "RPC_TIMEOUT",
        "The Solana RPC hostname lookup timed out.",
        true,
      )), timeoutMs);
      onAbort = () => reject(signal!.reason);
      signal?.addEventListener("abort", onAbort, { once: true });
    });
    // Node's lookup promise cannot be canceled. Stop awaiting it on interruption;
    // Promise.race also observes any late rejection without starting HTTPS.
    addresses = await Promise.race([
      Promise.resolve().then(() => {
        signal?.throwIfAborted();
        return lookup(url.hostname, { all: true, verbatim: true });
      }),
      interrupted,
    ]);
  } catch (error) {
    if (
      error instanceof PortfolioRpcError ||
      (signal?.aborted && Object.is(error, signal.reason))
    )
      throw error;
    throw new PortfolioRpcError(
      "RPC_DNS_REJECTED",
      "The configured RPC hostname could not be resolved safely.",
      true,
    );
  } finally {
    clearTimeout(timer);
    if (onAbort) signal?.removeEventListener("abort", onAbort);
  }
  if (
    addresses.length === 0 ||
    addresses.some((entry) => !isPublicRpcAddress(entry.address))
  ) {
    throw new PortfolioRpcError(
      "RPC_DNS_REJECTED",
      "The configured RPC hostname resolved outside the public network boundary.",
      false,
    );
  }
  const selected =
    addresses.find((entry) => entry.family === 4) ?? addresses[0];
  return {
    url,
    hostname: url.hostname,
    address: selected.address,
    family: selected.family as 4 | 6,
  };
}

function parseLosslessJson(source: string): unknown {
  try {
    return JSON.parse(source, ((
      _: string,
      value: unknown,
      context?: { source?: string },
    ) => {
      if (
        typeof value === "number" &&
        Number.isInteger(value) &&
        !Number.isSafeInteger(value) &&
        context?.source &&
        /^(0|[1-9]\d*)$/u.test(context.source)
      ) {
        return context.source;
      }
      return value;
    }) as (this: unknown, key: string, value: unknown) => unknown);
  } catch {
    throw new PortfolioRpcError(
      "RPC_RESPONSE_INVALID",
      "The RPC returned malformed JSON.",
      true,
    );
  }
}

async function postPinnedJson(
  endpoint: PinnedEndpoint,
  body: string,
  signal?: AbortSignal,
): Promise<{ status: number; headers: Record<string, string>; body: string }> {
  return new Promise((resolve, reject) => {
    const request = httpsRequest(
      endpoint.url,
      {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(body),
        },
        agent: false,
        signal,
        lookup: (_hostname, options, callback) => {
          if (typeof options === "object" && options.all) {
            callback(null, [
              { address: endpoint.address, family: endpoint.family },
            ]);
            return;
          }
          callback(null, endpoint.address, endpoint.family);
        },
      },
      (response) => {
        // A reset after headers is emitted by the response, not the request.
        response.on("error", reject);
        const chunks: Buffer[] = [];
        let size = 0;
        response.on("data", (chunk: Buffer) => {
          size += chunk.length;
          if (size > MAX_RPC_RESPONSE_BYTES) {
            request.destroy(
              new PortfolioRpcError(
                "RPC_RESPONSE_INVALID",
                "The RPC response exceeded the configured limit.",
                true,
              ),
            );
            return;
          }
          chunks.push(chunk);
        });
        response.on("end", () => {
          let decodedBody: string;
          try { decodedBody = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(Buffer.concat(chunks)); }
          catch { reject(new PortfolioRpcError("RPC_RESPONSE_INVALID", "The RPC returned malformed UTF-8.", true)); return; }
          const headers: Record<string, string> = {};
          for (const [name, value] of Object.entries(response.headers)) {
            if (typeof value === "string") headers[name] = value;
          }
          resolve({
            status: response.statusCode ?? 0,
            headers,
            body: decodedBody,
          });
        });
      },
    );
    request.on("error", reject);
    request.end(body);
  });
}

export async function createPinnedRpcCall(
  rawUrl: string | undefined,
  timeoutMs: number,
  signal?: AbortSignal,
): Promise<{ call: RpcCall; endpointHost: string }> {
  const endpoint = await pinRpcEndpoint(rawUrl, timeoutMs, signal);
  let nextId = 1;
  const call: RpcCall = async (method, params, parentSignal) => {
    const id = nextId++;
    const timeoutSignal = AbortSignal.timeout(timeoutMs);
    const signal = parentSignal
      ? AbortSignal.any([parentSignal, timeoutSignal])
      : timeoutSignal;
    let response;
    try {
      response = await postPinnedJson(
        endpoint,
        JSON.stringify({ jsonrpc: "2.0", id, method, params }),
        signal,
      );
    } catch (error) {
      if (signal.aborted) {
        throw new PortfolioRpcError(
          "RPC_TIMEOUT",
          "The Solana RPC request timed out.",
          true,
        );
      }
      if (error instanceof PortfolioRpcError) throw error;
      throw new PortfolioRpcError(
        "RPC_UNAVAILABLE",
        "The Solana RPC could not be reached.",
        true,
      );
    }
    const statusError = rpcHttpStatusError(response.status);
    if (statusError) throw statusError;
    const payload = record(parseLosslessJson(response.body), "RPC response");
    if (payload.id !== id || payload.jsonrpc !== "2.0") {
      throw new PortfolioRpcError(
        "RPC_RESPONSE_INVALID",
        "The RPC response identity did not match its request.",
        true,
      );
    }
    if (payload.error !== undefined) {
      throw new PortfolioRpcError(
        "RPC_UNAVAILABLE",
        `The Solana RPC rejected ${method}.`,
        true,
      );
    }
    if (!("result" in payload)) {
      throw new PortfolioRpcError(
        "RPC_RESPONSE_INVALID",
        `The Solana RPC omitted the ${method} result.`,
        true,
      );
    }
    return payload.result;
  };
  return { call, endpointHost: endpoint.hostname };
}

export function rpcHttpStatusError(status: number): PortfolioRpcError | null {
  if (status === 429) {
    return new PortfolioRpcError(
      "RPC_RATE_LIMITED",
      "The Solana RPC rate limit was reached. Try again later.",
      true,
    );
  }
  if (status < 200 || status >= 300) {
    return new PortfolioRpcError(
      "RPC_UNAVAILABLE",
      "The Solana RPC returned an unsuccessful HTTP status.",
      true,
    );
  }
  return null;
}

function contextResult(value: unknown, label: string): UnknownRecord {
  const result = record(value, label);
  const context = record(result.context, `${label}.context`);
  safeInteger(context.slot, `${label}.context.slot`);
  return result;
}

function parseTokenAccount(
  value: unknown,
  index: number,
  address: string,
  program: TokenProgram,
  programId: string,
): PortfolioTokenAccount {
  const label = `${program} account ${index}`;
  const row = record(value, label);
  const tokenAccount = publicKey(row.pubkey, `${label}.pubkey`);
  const account = record(row.account, `${label}.account`);
  if (publicKey(account.owner, `${label}.account.owner`) !== programId) {
    throw new PortfolioRpcError(
      "RPC_RESPONSE_INVALID",
      `${label} has an unexpected program owner.`,
      true,
    );
  }
  if (boolean(account.executable, `${label}.account.executable`)) {
    throw new PortfolioRpcError(
      "RPC_RESPONSE_INVALID",
      `${label} cannot be executable.`,
      true,
    );
  }
  const data = record(account.data, `${label}.account.data`);
  const expectedParser =
    program === "spl-token" ? "spl-token" : "spl-token-2022";
  if (data.program !== expectedParser) {
    throw new PortfolioRpcError(
      "RPC_RESPONSE_INVALID",
      `${label} used an unexpected parsed representation.`,
      true,
    );
  }
  const parsed = record(data.parsed, `${label}.account.data.parsed`);
  if (parsed.type !== "account") {
    throw new PortfolioRpcError(
      "RPC_RESPONSE_INVALID",
      `${label} is not a parsed token account.`,
      true,
    );
  }
  const info = record(parsed.info, `${label}.account.data.parsed.info`);
  const owner = publicKey(info.owner, `${label}.owner`);
  if (owner !== address) {
    throw new PortfolioRpcError(
      "RPC_RESPONSE_INVALID",
      `${label} does not belong to the requested wallet.`,
      true,
    );
  }
  const mint = publicKey(info.mint, `${label}.mint`);
  const state = text(info.state, `${label}.state`, 20);
  if (!["uninitialized", "initialized", "frozen"].includes(state)) {
    throw new PortfolioRpcError(
      "RPC_RESPONSE_INVALID",
      `${label} has an unsupported account state.`,
      true,
    );
  }
  const tokenAmount = record(info.tokenAmount, `${label}.tokenAmount`);
  const raw = u64(tokenAmount.amount, `${label}.tokenAmount.amount`);
  const decimals = safeInteger(
    tokenAmount.decimals,
    `${label}.tokenAmount.decimals`,
  );
  if (decimals > 255) {
    throw new PortfolioRpcError(
      "RPC_RESPONSE_INVALID",
      `${label} has unsupported token decimals.`,
      true,
    );
  }
  const extensionsValue = info.extensions;
  const extensions =
    extensionsValue === undefined
      ? []
      : (() => {
          if (!Array.isArray(extensionsValue)) {
            throw new PortfolioRpcError(
              "RPC_RESPONSE_INVALID",
              `${label}.extensions must be an array.`,
              true,
            );
          }
          return extensionsValue.map((extension, extensionIndex) =>
            text(
              record(extension, `${label}.extensions[${extensionIndex}]`)
                .extension,
              `${label}.extensions[${extensionIndex}].extension`,
              100,
            ),
          );
        })();
  return {
    tokenAccount,
    mint,
    owner,
    program,
    programId,
    rawAmount: raw.toString(),
    decimals,
    amount: formatBaseUnits(raw, decimals),
    state: state as PortfolioTokenAccount["state"],
    isNative: boolean(info.isNative, `${label}.isNative`),
    extensions,
  };
}

function aggregateMints(
  accounts: PortfolioTokenAccount[],
): PortfolioMintHolding[] {
  const totals = new Map<
    string,
    Omit<PortfolioMintHolding, "rawAmount" | "amount" | "accountCount"> & {
      raw: bigint;
      accountCount: number;
    }
  >();
  for (const account of accounts) {
    const existing = totals.get(account.mint);
    if (existing && existing.decimals !== account.decimals) {
      throw new PortfolioRpcError(
        "RPC_RESPONSE_INVALID",
        `Mint ${account.mint} returned inconsistent decimals.`,
        true,
      );
    }
    if (existing) {
      existing.raw += BigInt(account.rawAmount);
      if (existing.raw > MAX_U64) {
        throw new PortfolioRpcError("RPC_RESPONSE_INVALID", "Mint total exceeds u64.", true);
      }
      existing.accountCount += 1;
    } else {
      totals.set(account.mint, {
        mint: account.mint,
        program: account.program,
        programId: account.programId,
        decimals: account.decimals,
        raw: BigInt(account.rawAmount),
        accountCount: 1,
      });
    }
  }
  return Array.from(totals.values())
    .sort((left, right) => left.mint.localeCompare(right.mint))
    .map(({ raw, ...holding }) => ({
      ...holding,
      rawAmount: raw.toString(),
      amount: formatBaseUnits(raw, holding.decimals),
    }));
}

function parseProgramHoldings(
  value: unknown,
  address: string,
  program: TokenProgram,
  programId: string,
  allAccountIds: Set<string>,
): PortfolioProgramHoldings {
  const result = contextResult(value, `${program} response`);
  if (
    !Array.isArray(result.value) ||
    result.value.length > MAX_TOKEN_ACCOUNTS
  ) {
    throw new PortfolioRpcError(
      "RPC_RESPONSE_INVALID",
      `${program} response has an invalid account inventory.`,
      true,
    );
  }
  const accounts = result.value.map((row, index) => {
    const account = parseTokenAccount(row, index, address, program, programId);
    if (allAccountIds.has(account.tokenAccount)) {
      throw new PortfolioRpcError(
        "RPC_RESPONSE_INVALID",
        `Token account ${account.tokenAccount} was returned more than once.`,
        true,
      );
    }
    allAccountIds.add(account.tokenAccount);
    return account;
  });
  accounts.sort(
    (left, right) =>
      left.mint.localeCompare(right.mint) ||
      left.tokenAccount.localeCompare(right.tokenAccount),
  );
  return {
    program,
    programId,
    contextSlot: safeInteger(
      record(result.context, `${program} response.context`).slot,
      `${program} response.context.slot`,
    ),
    accounts,
    mints: aggregateMints(accounts),
  };
}

export async function readPortfolioWithRpc(
  addressInput: string,
  call: RpcCall,
  endpointHost: string,
  signal?: AbortSignal,
): Promise<PortfolioSuccess> {
  const address = validateWalletAddress(addressInput);
  signal?.throwIfAborted();
  const [genesisValue, balanceValue, splValue, token2022Value] =
    await Promise.all([
      call("getGenesisHash", [], signal),
      call("getBalance", [address, { commitment: RPC_COMMITMENT }], signal),
      call(
        "getTokenAccountsByOwner",
        [
          address,
          { programId: SPL_TOKEN_PROGRAM_ID },
          { encoding: "jsonParsed", commitment: RPC_COMMITMENT },
        ],
        signal,
      ),
      call(
        "getTokenAccountsByOwner",
        [
          address,
          { programId: TOKEN_2022_PROGRAM_ID },
          { encoding: "jsonParsed", commitment: RPC_COMMITMENT },
        ],
        signal,
      ),
    ]);
  signal?.throwIfAborted();
  const genesisHash = text(genesisValue, "genesis hash", 100);
  if (genesisHash !== MAINNET_GENESIS_HASH) {
    throw new PortfolioRpcError(
      "WRONG_CLUSTER",
      "The configured Solana RPC is not mainnet-beta.",
      false,
    );
  }
  const balance = contextResult(balanceValue, "balance response");
  const lamports = u64(balance.value, "balance response.value");
  const allAccountIds = new Set<string>();
  const splToken = parseProgramHoldings(
      splValue,
      address,
      "spl-token",
      SPL_TOKEN_PROGRAM_ID,
      allAccountIds,
  );
  const token2022 = parseProgramHoldings(
      token2022Value,
      address,
      "token-2022",
      TOKEN_2022_PROGRAM_ID,
      allAccountIds,
  );
  const splMints = new Set(splToken.mints.map((mint) => mint.mint));
  if (token2022.mints.some((mint) => splMints.has(mint.mint))) {
    throw new PortfolioRpcError("RPC_RESPONSE_INVALID", "A mint was reported under both token programs.", true);
  }
  return {
    ok: true,
    address,
    cluster: "mainnet-beta",
    genesisHash,
    commitment: RPC_COMMITMENT,
    observedAt: new Date().toISOString(),
    endpointHost,
    sol: {
      lamports: lamports.toString(),
      amount: formatBaseUnits(lamports, 9),
      contextSlot: safeInteger(
        record(balance.context, "balance response.context").slot,
        "balance response.context.slot",
      ),
    },
    splToken,
    token2022,
    snapshotAtomic: false,
  };
}

export async function readLivePortfolio(
  address: string,
  options: {
    rpcUrl?: string;
    timeoutMs?: number;
    signal?: AbortSignal;
  } = {},
): Promise<PortfolioSuccess> {
  const canonicalAddress = validateWalletAddress(address);
  const { call, endpointHost } = await createPinnedRpcCall(
    options.rpcUrl === undefined ? process.env.SOLANA_RPC_URL : options.rpcUrl,
    options.timeoutMs ?? 10_000,
    options.signal,
  );
  return readPortfolioWithRpc(canonicalAddress, call, endpointHost, options.signal);
}
