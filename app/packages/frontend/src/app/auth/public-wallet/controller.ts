/** Wallet Standard public-address connection only. No signing/auth/session port exists. */
type RecordValue = Record<string, unknown>;
const record = (value: unknown): value is RecordValue =>
  value !== null && typeof value === "object";
const alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";

/** Canonical base58 encoding of exactly 32 bytes; no curve/ownership claim. */
export function publicAddress(value: unknown): string {
  if (typeof value !== "string" || value.length < 32 || value.length > 44)
    throw new Error("Invalid public address");
  const bytes = [0];
  for (const character of value) {
    let carry = alphabet.indexOf(character);
    if (carry < 0) throw new Error("Invalid public address");
    for (let i = 0; i < bytes.length; i++) {
      carry += bytes[i] * 58;
      bytes[i] = carry & 255;
      carry >>= 8;
    }
    while (carry) {
      bytes.push(carry & 255);
      carry >>= 8;
    }
  }
  let leading = 0;
  while (value[leading] === "1") leading++;
  if (
    (bytes.length === 1 && bytes[0] === 0 ? 0 : bytes.length) + leading !==
    32
  )
    throw new Error("Invalid public address");
  return value;
}

type Feature = { version: "1.0.0"; [key: string]: unknown };
type Wallet = {
  name: string;
  raw: RecordValue;
  connect: Feature & { connect(): Promise<unknown> };
  events: Feature & {
    on(event: "change", callback: (change: unknown) => void): () => void;
  };
};
export type WalletChoice = Readonly<{ id: number; name: string }>;
export type PublicWalletState = Readonly<{
  status:
    | "idle"
    | "choosing"
    | "connecting"
    | "connected"
    | "disconnecting"
    | "error";
  wallets: readonly WalletChoice[];
  selected: number | null;
  address: string | null;
  message: string | null;
}>;
const initial: PublicWalletState = Object.freeze({
  status: "idle",
  wallets: [],
  selected: null,
  address: null,
  message: null,
});

function supported(raw: unknown): Wallet | null {
  try {
    if (
      !record(raw) ||
      raw.version !== "1.0.0" ||
      typeof raw.name !== "string" ||
      !raw.name.trim() ||
      raw.name.length > 80 ||
      /[\p{C}]/u.test(raw.name) ||
      !Array.isArray(raw.chains) ||
      !raw.chains.some(
        (chain) => typeof chain === "string" && chain.startsWith("solana:"),
      ) ||
      !record(raw.features)
    )
      return null;
    const connect = raw.features["standard:connect"],
      events = raw.features["standard:events"];
    if (
      !record(connect) ||
      connect.version !== "1.0.0" ||
      typeof connect.connect !== "function" ||
      !record(events) ||
      events.version !== "1.0.0" ||
      typeof events.on !== "function"
    )
      return null;
    return {
      name: raw.name,
      raw,
      connect: connect as Wallet["connect"],
      events: events as Wallet["events"],
    };
  } catch {
    return null;
  }
}

/** One opt-in dialog lifetime. Closing it drops all addresses and listeners. */
export class PublicWalletController {
  private state = initial;
  private listeners = new Set<() => void>();
  private wallets = new Map<number, Wallet>();
  private ids = new Map<unknown, number>();
  private nextId = 0;
  private generation = 0;
  private stopRegistry: (() => void) | null = null;
  private stopChanges: (() => void) | null = null;
  private timeout: ReturnType<typeof setTimeout> | null = null;
  private target: EventTarget;
  private timeoutMs: number;
  constructor(target: EventTarget, timeoutMs = 15_000) {
    this.target = target;
    this.timeoutMs = timeoutMs;
  }
  getSnapshot = () => this.state;
  subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };
  private publish(next: Partial<PublicWalletState>) {
    this.state = Object.freeze({ ...this.state, ...next });
    for (const listener of this.listeners) listener();
  }
  private choices() {
    return [...this.wallets].map(([id, wallet]) => ({ id, name: wallet.name }));
  }
  private clearAttempt() {
    this.generation++;
    if (this.timeout !== null) clearTimeout(this.timeout);
    this.timeout = null;
    const stop = this.stopChanges;
    this.stopChanges = null;
    try {
      stop?.();
    } catch {
      /* Provider cleanup cannot preserve the local address. */
    }
  }
  private fail(message: string) {
    this.clearAttempt();
    this.publish({ status: "error", address: null, selected: null, message });
  }
  discover = () => {
    if (this.stopRegistry) return;
    let active = true;
    const register = (...candidates: unknown[]) => {
      if (!active) return () => {};
      const added: number[] = [];
      for (const raw of candidates) {
        if (this.ids.has(raw) || this.wallets.size >= 100) continue;
        const wallet = supported(raw);
        if (!wallet) continue;
        const id = this.nextId++;
        this.ids.set(raw, id);
        this.wallets.set(id, wallet);
        added.push(id);
      }
      this.publish({ wallets: this.choices() });
      return () => {
        if (!active) return;
        for (const id of added) {
          const wallet = this.wallets.get(id);
          this.wallets.delete(id);
          if (wallet) this.ids.delete(wallet.raw);
          if (this.state.selected === id)
            this.fail("Wallet is no longer available.");
        }
        this.publish({ wallets: this.choices() });
      };
    };
    const api = Object.freeze({ register });
    const receive = (event: Event) => {
      try {
        const callback = (event as CustomEvent<unknown>).detail;
        if (typeof callback === "function") callback(api);
      } catch {
        /* An invalid extension must not stop other wallets. */
      }
    };
    this.target.addEventListener("wallet-standard:register-wallet", receive);
    this.stopRegistry = () => {
      active = false;
      this.target.removeEventListener(
        "wallet-standard:register-wallet",
        receive,
      );
    };
    this.publish({ status: "choosing", message: null });
    if (!active) return;
    this.target.dispatchEvent(
      new CustomEvent("wallet-standard:app-ready", { detail: api }),
    );
  };
  private address(wallet: Wallet) {
    const accounts = wallet.raw.accounts;
    if (!Array.isArray(accounts)) throw new Error("No Solana account");
    const account = accounts.find(
      (candidate) =>
        record(candidate) &&
        Array.isArray(candidate.chains) &&
        candidate.chains.some(
          (chain: unknown) =>
            typeof chain === "string" && chain.startsWith("solana:"),
        ),
    );
    if (!record(account)) throw new Error("No Solana account");
    return publicAddress(account.address);
  }
  connect = async (id: number) => {
    if (
      this.state.status === "connecting" ||
      this.state.status === "connected" ||
      this.state.status === "disconnecting"
    )
      return;
    const stored = this.wallets.get(id);
    const wallet = stored && supported(stored.raw);
    if (!wallet) {
      this.fail("Wallet is no longer available.");
      return;
    }
    this.clearAttempt();
    const generation = this.generation;
    this.publish({
      status: "connecting",
      selected: id,
      address: null,
      message: null,
    });
    if (generation !== this.generation) return;
    this.timeout = setTimeout(() => {
      if (generation === this.generation)
        this.fail("Connection timed out. You can try again.");
    }, this.timeoutMs);
    try {
      // Explicit action only: no silent connect, signIn, signMessage or transaction access.
      await wallet.connect.connect();
      if (generation !== this.generation) return;
      this.address(wallet);
      if (this.timeout !== null) clearTimeout(this.timeout);
      this.timeout = null;
      const stop = wallet.events.on("change", (change) => {
        if (generation !== this.generation) return;
        try {
          if (record(change) && "accounts" in change)
            this.publish({ address: this.address(wallet) });
          if (!supported(wallet.raw))
            this.fail("Wallet connection is no longer available.");
        } catch {
          this.fail("Wallet account is no longer available.");
        }
      });
      if (typeof stop !== "function")
        throw new Error("Invalid event subscription");
      // A synchronous change callback may have invalidated this attempt.
      if (generation !== this.generation) {
        try {
          stop();
        } catch {}
        return;
      }
      this.stopChanges = stop;
      this.publish({ status: "connected", address: this.address(wallet) });
    } catch {
      if (generation === this.generation)
        this.fail("Unable to connect. The request may have been declined.");
    }
  };
  forget = () => {
    this.clearAttempt();
    this.publish({
      status: "choosing",
      selected: null,
      address: null,
      message: null,
    });
  };
  disconnect = async () => {
    if (this.state.status === "disconnecting") return;
    const wallet =
      this.state.selected === null
        ? null
        : this.wallets.get(this.state.selected);
    this.clearAttempt();
    const generation = this.generation;
    this.publish({ status: "disconnecting", selected: null, address: null, message: null });
    if (generation !== this.generation) return;
    this.timeout = setTimeout(() => {
      if (generation === this.generation)
        this.fail("Address forgotten. The wallet disconnect timed out.");
    }, this.timeoutMs);
    try {
      const features = wallet?.raw.features;
      const feature = record(features) ? features["standard:disconnect"] : null;
      if (
        record(feature) &&
        feature.version === "1.0.0" &&
        typeof feature.disconnect === "function"
      )
        await feature.disconnect();
      else if (generation === this.generation)
        this.publish({
          message:
            "Address forgotten. The wallet connection may remain active. Manage it in your wallet.",
        });
    } catch {
      if (generation === this.generation)
        this.publish({
          message: "Address forgotten. The wallet could not disconnect.",
        });
    } finally {
      if (generation === this.generation) {
        if (this.timeout !== null) clearTimeout(this.timeout);
        this.timeout = null;
        this.publish({ status: "choosing" });
      }
    }
  };
  dispose = () => {
    this.clearAttempt();
    this.stopRegistry?.();
    this.stopRegistry = null;
    this.wallets.clear();
    this.ids.clear();
    this.publish(initial);
  };
}
