"use client";

import { useEffect, useRef, useState } from "react";
import {
  readPdaBalances as readPublicBalances,
  PublicBalanceError,
} from "../../holder-rewards/read-balances";
import type { PortfolioSuccess } from "../../portfolio/types";
import styles from "./public-wallet.module.css";

type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ready"; value: PortfolioSuccess }
  | { status: "error"; message: string };

function inventoryText(accounts: number, mints: number): string {
  return `${accounts} ${accounts === 1 ? "account" : "accounts"} · ${mints} ${mints === 1 ? "mint" : "mints"}`;
}

function failureMessage(error: unknown): string {
  if (error instanceof PublicBalanceError) {
    if (
      error.message ===
      "The public RPC service is rate limited. Try again later."
    )
      return error.message;
    if (error.message === "The public balance request timed out. Try again.")
      return error.message;
  }
  return "The public mainnet overview is unavailable. Try again.";
}

/** The shared reader accepts any public address; it does not derive a PDA. */
export function PublicWalletBalanceOverview({ address }: { address: string }) {
  const [state, setState] = useState<State>({ status: "idle" });
  const generation = useRef(0);
  const active = useRef<AbortController | null>(null);
  const deadline = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setState({ status: "idle" });
    return () => {
      generation.current++;
      active.current?.abort();
      if (deadline.current) clearTimeout(deadline.current);
    };
  }, [address]);

  async function read() {
    active.current?.abort();
    if (deadline.current) clearTimeout(deadline.current);
    const controller = new AbortController();
    active.current = controller;
    const request = ++generation.current;
    setState({ status: "loading" });
    const timeout = setTimeout(() => {
      if (request !== generation.current) return;
      controller.abort();
      setState({
        status: "error",
        message: "The public balance request timed out. Try again.",
      });
    }, 20_000);
    deadline.current = timeout;
    try {
      const value = await readPublicBalances(address, {
        signal: controller.signal,
      });
      if (!controller.signal.aborted && request === generation.current)
        setState({ status: "ready", value });
    } catch (error) {
      if (!controller.signal.aborted && request === generation.current)
        setState({ status: "error", message: failureMessage(error) });
    } finally {
      clearTimeout(timeout);
      if (deadline.current === timeout) deadline.current = null;
    }
  }

  const value =
    state.status === "ready" && state.value.address === address
      ? state.value
      : null;
  return (
    <section
      className={styles.overview}
      aria-label="Public mainnet overview"
      data-testid="public-wallet-balance-overview"
    >
      <h4>Public mainnet overview</h4>
      <p>
        Read public SOL holdings and token-account inventory for this address
        from the configured mainnet RPC. Your wallet may be using another
        network.
      </p>
      <button
        type="button"
        className={styles.action}
        disabled={state.status === "loading"}
        onClick={read}
      >
        {state.status === "loading"
          ? "Reading public mainnet…"
          : value
            ? "Refresh public mainnet overview"
            : "Read public mainnet overview"}
      </button>
      {state.status === "loading" && (
        <p role="status">Reading public balances…</p>
      )}
      {state.status === "error" && <p role="alert">{state.message}</p>}
      {value && (
        <div
          className={styles.observation}
          data-testid="public-wallet-balance-result"
        >
          <dl>
            <div>
              <dt>SOL holdings</dt>
              <dd>{value.sol.amount} SOL</dd>
            </div>
            <div>
              <dt>SPL Token inventory</dt>
              <dd>
                {inventoryText(
                  value.splToken.accounts.length,
                  value.splToken.mints.length,
                )}
              </dd>
            </div>
            <div>
              <dt>Token-2022 inventory</dt>
              <dd>
                {inventoryText(
                  value.token2022.accounts.length,
                  value.token2022.mints.length,
                )}
              </dd>
            </div>
          </dl>
          <p>
            Observed <time dateTime={value.observedAt}>{value.observedAt}</time>{" "}
            via {value.endpointHost}.
          </p>
          <p>
            Confirmed slots: SOL {value.sol.contextSlot}, SPL{" "}
            {value.splToken.contextSlot}, Token-2022{" "}
            {value.token2022.contextSlot}. These independent reads are not an
            atomic snapshot.
          </p>
          <p>
            Inventory counts are not monetary totals. Holdings do not establish
            ownership, spendability, rewards or profit.
          </p>
        </div>
      )}
    </section>
  );
}
