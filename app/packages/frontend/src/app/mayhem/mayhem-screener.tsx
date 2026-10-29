"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  buildMayhemQuery,
  MAYHEM_FILTERS,
  MAYHEM_SORTS,
  parseMayhemResponse,
  sortMayhemCoins,
  type MayhemCoin,
  type MayhemFilter,
  type MayhemSort,
} from "./mayhem-data";

const FILTER_LABELS: Record<MayhemFilter, string> = {
  all: "All",
  active: "Active",
  paused: "Paused",
  ended: "Ended",
};

const SORT_LABELS: Record<MayhemSort, string> = {
  lastTraded: "Last traded",
  volume: "24h volume",
  mcap: "Market cap",
  newest: "Newest",
};

type LoadState =
  | { kind: "loading" }
  | { kind: "unavailable"; message: string }
  | { kind: "invalid" }
  | { kind: "success"; coins: MayhemCoin[] };

function hrefFor(filter: MayhemFilter, sort: MayhemSort) {
  const query = new URLSearchParams();
  if (filter !== "all") query.set("state", filter);
  if (sort !== "lastTraded") query.set("sort", sort);
  const encoded = query.toString();
  return encoded ? `/mayhem?${encoded}` : "/mayhem";
}

function money(value: number | undefined) {
  if (value === undefined) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function date(value: number | undefined) {
  if (value === undefined) return "—";
  const parsed = new Date(value);
  return Number.isFinite(parsed.getTime())
    ? new Intl.DateTimeFormat("en-US", { dateStyle: "medium" }).format(parsed)
    : "—";
}

function CoinRows({ coins }: { coins: readonly MayhemCoin[] }) {
  return (
    <div
      className="mayhem-results"
      role="region"
      aria-label="Mayhem coin results"
    >
      {coins.map((coin, index) => (
        <article
          className="mayhem-row"
          key={coin.mint}
          data-testid="mayhem-coin-row"
        >
          <span className="mayhem-rank" aria-label={`Rank ${index + 1}`}>
            {index + 1}
          </span>
          <div className="mayhem-identity">
            <span className="mayhem-avatar" aria-hidden="true">
              {coin.symbol.slice(0, 2).toUpperCase()}
            </span>
            <div>
              <h2>{coin.name}</h2>
              <p>{coin.symbol}</p>
              <code>{coin.mint}</code>
            </div>
          </div>
          <dl className="mayhem-metrics">
            <div>
              <dt>Market cap</dt>
              <dd>{money(coin.marketCapUsd)}</dd>
            </div>
            <div>
              <dt>24h volume</dt>
              <dd>{money(coin.volumeUsd24h)}</dd>
            </div>
            <div>
              <dt>State</dt>
              <dd>{coin.state ?? "Unavailable"}</dd>
            </div>
            <div>
              <dt>Mode</dt>
              <dd>{coin.mode ?? "Unavailable"}</dd>
            </div>
            <div>
              <dt>Created</dt>
              <dd>{date(coin.createdTimestamp)}</dd>
            </div>
          </dl>
        </article>
      ))}
    </div>
  );
}

export default function MayhemScreener({
  initialFilter,
  initialSort,
}: {
  initialFilter: MayhemFilter;
  initialSort: MayhemSort;
}) {
  const router = useRouter();
  const [loadState, setLoadState] = useState<LoadState>({ kind: "loading" });
  const [retry, setRetry] = useState(0);
  const requestSequence = useRef(0);
  const pendingSelection = useRef({ filter: initialFilter, sort: initialSort });

  useEffect(() => {
    pendingSelection.current = { filter: initialFilter, sort: initialSort };
  }, [initialFilter, initialSort]);

  function navigate(
    changes: Partial<{ filter: MayhemFilter; sort: MayhemSort }>,
  ) {
    const next = { ...pendingSelection.current, ...changes };
    pendingSelection.current = next;
    router.push(hrefFor(next.filter, next.sort));
  }

  useEffect(() => {
    const sequence = ++requestSequence.current;
    const controller = new AbortController();
    setLoadState({ kind: "loading" });
    const query = buildMayhemQuery({ filter: initialFilter });
    query.set("filter", initialFilter);

    void fetch(`/api/mayhem-screener?${query}`, {
      method: "GET",
      headers: { Accept: "application/json" },
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          const body = (await response.json().catch(() => null)) as {
            message?: unknown;
          } | null;
          const message =
            typeof body?.message === "string"
              ? body.message
              : "Mayhem data is unavailable.";
          if (sequence === requestSequence.current)
            setLoadState({ kind: "unavailable", message });
          return;
        }
        const parsed = parseMayhemResponse(await response.json());
        if (sequence === requestSequence.current)
          setLoadState({ kind: "success", coins: parsed.coins });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted || sequence !== requestSequence.current)
          return;
        setLoadState(
          error instanceof Error && error.name === "MayhemDataError"
            ? { kind: "invalid" }
            : {
                kind: "unavailable",
                message: "The local read-only adapter could not be reached.",
              },
        );
      });

    return () => controller.abort();
  }, [initialFilter, retry]);

  const coins = useMemo(
    () =>
      loadState.kind === "success"
        ? sortMayhemCoins(loadState.coins, initialSort)
        : [],
    [initialSort, loadState],
  );

  return (
    <section className="mayhem-page" aria-labelledby="mayhem-title">
      <header className="mayhem-header">
        <div>
          <p className="eyebrow">Evidence-backed reconstruction</p>
          <h1 id="mayhem-title">Mayhem screener</h1>
          <p className="description">
            Filter and sort the captured Mayhem coin contract without enabling
            trading or presenting invented live market data.
          </p>
        </div>
        <div className="mayhem-boundary">
          <strong>Read only</strong>
          <span>No qualified live dataset</span>
        </div>
      </header>

      <aside className="mayhem-notice" aria-label="Data availability">
        The original client contract is reconstructed, but no archived Mayhem
        response is checked in. Production therefore fails closed instead of
        contacting the captured API origin.
      </aside>

      <div className="mayhem-toolbar">
        <nav className="mayhem-tabs" aria-label="Mayhem state filter">
          {MAYHEM_FILTERS.map((filter) => (
            <Link
              key={filter}
              href={hrefFor(filter, initialSort)}
              onNavigate={(event) => {
                event.preventDefault();
                navigate({ filter });
              }}
              aria-current={filter === initialFilter ? "page" : undefined}
              data-selected={filter === initialFilter}
            >
              {FILTER_LABELS[filter]}
            </Link>
          ))}
        </nav>
        <label className="mayhem-sort">
          <span>Sort by</span>
          <select
            aria-label="Sort Mayhem coins"
            value={initialSort}
            onChange={(event) =>
              navigate({ sort: event.target.value as MayhemSort })
            }
          >
            {MAYHEM_SORTS.map((sort) => (
              <option value={sort} key={sort}>
                {SORT_LABELS[sort]}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div aria-live="polite">
        {loadState.kind === "loading" ? (
          <section className="mayhem-state" data-testid="mayhem-loading">
            <span className="mayhem-spinner" aria-hidden="true" />
            <h2>Loading local screener data</h2>
            <p>Checking the read-only data boundary.</p>
          </section>
        ) : loadState.kind === "invalid" ? (
          <section
            className="mayhem-state mayhem-state--error"
            role="alert"
            data-testid="mayhem-validation-error"
          >
            <h2>Mayhem data failed validation</h2>
            <p>
              The response was rejected. No partial or fabricated rows are
              displayed.
            </p>
          </section>
        ) : loadState.kind === "unavailable" ? (
          <section className="mayhem-state" data-testid="mayhem-unavailable">
            <h2>Screener data unavailable offline</h2>
            <p>{loadState.message}</p>
            <button
              type="button"
              onClick={() => setRetry((value) => value + 1)}
            >
              Retry local adapter
            </button>
          </section>
        ) : coins.length === 0 ? (
          <section className="mayhem-state" data-testid="mayhem-empty">
            <h2>No qualified local results</h2>
            <p>
              The selected state returned no records in this test-backed data
              source. This says nothing about the live Pump market.
            </p>
          </section>
        ) : (
          <>
            <p
              className="mayhem-test-disclosure"
              data-testid="mayhem-test-disclosure"
            >
              Synthetic browser fixture — not live Pump activity
            </p>
            <CoinRows coins={coins} />
          </>
        )}
      </div>

      <footer className="mayhem-provenance">
        Captured contract:{" "}
        <code>GET {"https://frontend-api-v3.pump.fun/coins/mayhem-mode"}</code>.
        No production request is issued by this reconstruction.
      </footer>
    </section>
  );
}
