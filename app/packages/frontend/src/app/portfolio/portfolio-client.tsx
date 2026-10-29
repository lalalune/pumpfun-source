"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useRef, useState } from "react";
import { PublicWalletRecordPanel } from "../wallet-program-record/panel";
import {
  isPortfolioResponse,
  type PortfolioMintHolding,
  type PortfolioProgramHoldings,
  type PortfolioResponse,
  type PortfolioSuccess,
} from "./types";

type LoadState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; value: PortfolioSuccess }
  | {
      status: "error";
      error: { code: string; message: string; retryable: boolean };
    };

function shortened(value: string): string {
  return `${value.slice(0, 8)}…${value.slice(-8)}`;
}

function CopyButton({ value, label }: { value: string; label: string }) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }
  return (
    <button
      className="portfolio-copy"
      type="button"
      aria-label={`Copy ${label}`}
      onClick={copy}
    >
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function MintSummary({ holding }: { holding: PortfolioMintHolding }) {
  return (
    <article className="portfolio-mint-card">
      <header>
        <span>
          {holding.program === "spl-token" ? "SPL Token" : "Token-2022"}
        </span>
        <strong>{holding.amount}</strong>
      </header>
      <div className="portfolio-address-line">
        <code title={holding.mint}>{shortened(holding.mint)}</code>
        <CopyButton value={holding.mint} label="token mint address" />
      </div>
      <dl>
        <div>
          <dt>Raw amount</dt>
          <dd>{holding.rawAmount}</dd>
        </div>
        <div>
          <dt>Decimals</dt>
          <dd>{holding.decimals}</dd>
        </div>
        <div>
          <dt>Token accounts</dt>
          <dd>{holding.accountCount}</dd>
        </div>
      </dl>
    </article>
  );
}

function ProgramHoldings({ holdings }: { holdings: PortfolioProgramHoldings }) {
  const title = holdings.program === "spl-token" ? "SPL Token" : "Token-2022";
  return (
    <section
      className="portfolio-program"
      aria-labelledby={`${holdings.program}-heading`}
    >
      <div className="portfolio-section-heading">
        <div>
          <h2 id={`${holdings.program}-heading`}>{title} holdings</h2>
          <p>
            {holdings.mints.length} mints across {holdings.accounts.length}{" "}
            token accounts
          </p>
        </div>
        <span>Slot {holdings.contextSlot.toLocaleString("en-US")}</span>
      </div>

      {holdings.accounts.length === 0 ? (
        <div className="portfolio-empty-program">
          No {title} accounts were returned for this wallet at the observed
          slot.
        </div>
      ) : (
        <>
          <div className="portfolio-mint-grid">
            {holdings.mints.map((holding) => (
              <MintSummary
                key={`${holding.programId}:${holding.mint}`}
                holding={holding}
              />
            ))}
          </div>
          <div className="portfolio-table-wrap">
            <table className="portfolio-table">
              <caption>
                {title} token accounts; each account remains a separate row.
              </caption>
              <thead>
                <tr>
                  <th scope="col">Token account</th>
                  <th scope="col">Mint</th>
                  <th scope="col">Exact quantity</th>
                  <th scope="col">Raw amount</th>
                  <th scope="col">State</th>
                </tr>
              </thead>
              <tbody>
                {holdings.accounts.map((account) => (
                  <tr key={account.tokenAccount}>
                    <td>
                      <div className="portfolio-table-address">
                        <code title={account.tokenAccount}>
                          {shortened(account.tokenAccount)}
                        </code>
                        <CopyButton
                          value={account.tokenAccount}
                          label="token-account address"
                        />
                      </div>
                    </td>
                    <td>
                      <div className="portfolio-table-address">
                        <code title={account.mint}>
                          {shortened(account.mint)}
                        </code>
                        <CopyButton
                          value={account.mint}
                          label="token mint address"
                        />
                      </div>
                    </td>
                    <td>{account.amount}</td>
                    <td>{account.rawAmount}</td>
                    <td>
                      <span
                        className={`portfolio-state portfolio-state--${account.state}`}
                      >
                        {account.state}
                      </span>
                      {account.extensions.length > 0 ? (
                        <small>{account.extensions.join(", ")}</small>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}

function PortfolioResult({ value }: { value: PortfolioSuccess }) {
  const isEmpty =
    value.sol.lamports === "0" &&
    value.splToken.accounts.length === 0 &&
    value.token2022.accounts.length === 0;
  return (
    <div className="portfolio-result" data-testid="portfolio-result">
      <section
        className="portfolio-observation"
        aria-labelledby="portfolio-observation-heading"
      >
        <div>
          <p className="eyebrow">Verified cluster</p>
          <h2 id="portfolio-observation-heading">Solana mainnet-beta</h2>
          <p>
            Confirmed commitment observed{" "}
            {new Date(value.observedAt).toLocaleString()} via{" "}
            <code>{value.endpointHost}</code>.
          </p>
        </div>
        <dl>
          <div>
            <dt>SOL context slot</dt>
            <dd>{value.sol.contextSlot.toLocaleString("en-US")}</dd>
          </div>
          <div>
            <dt>SPL context slot</dt>
            <dd>{value.splToken.contextSlot.toLocaleString("en-US")}</dd>
          </div>
          <div>
            <dt>Token-2022 context slot</dt>
            <dd>{value.token2022.contextSlot.toLocaleString("en-US")}</dd>
          </div>
        </dl>
        <p className="portfolio-nonatomic">
          These independent RPC calls may observe different slots. This is not
          an atomic account snapshot.
        </p>
      </section>

      <section
        className="portfolio-sol-card"
        aria-labelledby="sol-balance-heading"
      >
        <div>
          <p className="eyebrow">Native balance</p>
          <h2 id="sol-balance-heading">{value.sol.amount} SOL</h2>
        </div>
        <dl>
          <div>
            <dt>Lamports</dt>
            <dd>{value.sol.lamports}</dd>
          </div>
          <div>
            <dt>Wallet</dt>
            <dd>
              <code title={value.address}>{shortened(value.address)}</code>
            </dd>
          </div>
        </dl>
      </section>

      {isEmpty ? (
        <section className="portfolio-empty-wallet">
          <h2>No on-chain holdings returned</h2>
          <p>
            This wallet had zero lamports and no SPL or Token-2022 accounts at
            the three reported context slots.
          </p>
        </section>
      ) : null}

      <ProgramHoldings holdings={value.splToken} />
      <ProgramHoldings holdings={value.token2022} />

      <p className="portfolio-disclosure">
        Mint totals sum only the token accounts returned by each program query.
        Separate token accounts remain listed below each total. No symbols,
        prices, USD values, Pump positions, realized PnL or token legitimacy
        claims are inferred from RPC balances.
      </p>
      <PublicWalletRecordPanel key={value.address} address={value.address} />
    </div>
  );
}

export default function PortfolioClient({
  initialAddress,
}: {
  initialAddress: string;
}) {
  const router = useRouter();
  const [draft, setDraft] = useState(initialAddress);
  const draftVersion = useRef(0);
  const pendingNavigation = useRef<{
    address: string;
    version: number;
  } | null>(null);
  const [refreshVersion, setRefreshVersion] = useState(0);
  const [loaded, setLoaded] = useState<{ address: string; state: LoadState }>({
    address: initialAddress,
    state: initialAddress ? { status: "loading" } : { status: "idle" },
  });
  const state: LoadState =
    loaded.address === initialAddress
      ? loaded.state
      : initialAddress
        ? { status: "loading" }
        : { status: "idle" };
  const requestSequence = useRef(0);

  useEffect(() => {
    const pending = pendingNavigation.current;
    pendingNavigation.current = null;
    // A completed local navigation must not erase edits made after submission.
    if (
      pending?.address !== initialAddress ||
      pending.version === draftVersion.current
    ) {
      setDraft(initialAddress);
    }
  }, [initialAddress]);

  useEffect(() => {
    const onPopState = () => {
      pendingNavigation.current = null;
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    const sequence = ++requestSequence.current;
    const setState = (state: LoadState) =>
      setLoaded({ address: initialAddress, state });
    if (!initialAddress) {
      setState({ status: "idle" });
      return;
    }
    const controller = new AbortController();
    setState({ status: "loading" });
    void (async () => {
      try {
        const response = await fetch(
          `/api/portfolio?${new URLSearchParams({ address: initialAddress })}`,
          {
            method: "GET",
            headers: { Accept: "application/json" },
            cache: "no-store",
            signal: controller.signal,
          },
        );
        const payload: unknown = await response.json();
        if (!isPortfolioResponse(payload, initialAddress.trim())) {
          throw new Error(
            "The portfolio endpoint returned an invalid response.",
          );
        }
        if (controller.signal.aborted || sequence !== requestSequence.current)
          return;
        if (payload.ok) setState({ status: "success", value: payload });
        else setState({ status: "error", error: payload.error });
      } catch (error) {
        if (controller.signal.aborted || sequence !== requestSequence.current)
          return;
        setState({
          status: "error",
          error: {
            code: "NETWORK_FAILURE",
            message:
              error instanceof Error
                ? error.message
                : "The live portfolio request failed.",
            retryable: true,
          },
        });
      }
    })();
    return () => controller.abort();
  }, [initialAddress, refreshVersion]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const address = draft.trim();
    pendingNavigation.current =
      address === initialAddress
        ? null
        : { address, version: draftVersion.current };
    if (!address) {
      router.push("/portfolio");
      return;
    }
    if (address === initialAddress) {
      setRefreshVersion((value) => value + 1);
      return;
    }
    router.push(`/portfolio?${new URLSearchParams({ address })}`);
  }

  function clear() {
    draftVersion.current += 1;
    pendingNavigation.current = initialAddress
      ? { address: "", version: draftVersion.current }
      : null;
    setDraft("");
    router.push("/portfolio");
  }

  return (
    <>
      <form
        className="portfolio-form"
        aria-label="Load public Solana wallet"
        onSubmit={submit}
      >
        <label htmlFor="portfolio-address">Solana public-key address</label>
        <div className="portfolio-input-row">
          <input
            id="portfolio-address"
            name="address"
            type="text"
            inputMode="text"
            autoComplete="off"
            spellCheck={false}
            placeholder="Enter a public Solana address"
            value={draft}
            onChange={(event) => {
              draftVersion.current += 1;
              setDraft(event.target.value);
            }}
          />
          {draft ? (
            <button
              className="portfolio-secondary-button"
              type="button"
              onClick={clear}
            >
              Clear
            </button>
          ) : null}
          <button className="portfolio-primary-button" type="submit">
            {state.status === "success" && draft.trim() === initialAddress
              ? "Refresh live balances"
              : "Load wallet"}
          </button>
        </div>
        <p>
          Only public account data is read. Never enter a private key or seed
          phrase.
        </p>
      </form>

      {state.status === "idle" ? (
        <section className="portfolio-intro" data-testid="portfolio-idle">
          <h2>Live balances, without a wallet connection</h2>
          <p>
            Enter any public Solana address. Results come from mainnet RPC at
            request time; this page never substitutes historical or synthetic
            holdings.
          </p>
        </section>
      ) : null}
      {state.status === "loading" ? (
        <section className="portfolio-loading" role="status" aria-live="polite">
          <span aria-hidden="true" />
          <div>
            <h2>Reading Solana mainnet</h2>
            <p>
              Checking cluster identity, SOL, SPL Token and Token-2022 accounts…
            </p>
          </div>
        </section>
      ) : null}
      {state.status === "error" ? (
        <section
          className="portfolio-error"
          role="alert"
          data-error-code={state.error.code}
        >
          <h2>
            {state.error.code === "RPC_RATE_LIMITED"
              ? "RPC rate limit reached"
              : "Live portfolio unavailable"}
          </h2>
          <p>{state.error.message}</p>
          <small>
            No cached, historical or synthetic holdings were substituted.
          </small>
          {state.error.retryable ? (
            <button
              className="portfolio-secondary-button"
              type="button"
              onClick={() => setRefreshVersion((value) => value + 1)}
            >
              Try again
            </button>
          ) : null}
        </section>
      ) : null}
      {state.status === "success" ? (
        <PortfolioResult value={state.value} />
      ) : null}
    </>
  );
}
