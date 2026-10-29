"use client";

import Link from "next/link";
import {
  creatorPagination,
  CREATOR_LEADERBOARD_LIMIT,
} from "./creator-pagination";
import { CompetitionCountdown } from "../../components/leaderboard/CompetitionCountdown";
import { useSearchParams } from "next/navigation";
import {
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  competitionStatuses,
  creatorPeriods,
  leaderboardCategories,
  parseLeaderboardResponse,
  traderPeriods,
  traderSorts,
  type CompetitionDetailData,
  type CompetitionEntry,
  type CompetitionStatus,
  type CompetitionSummary,
  type CompetitionsData,
  type CreatorEntry,
  type CreatorsData,
  type LeaderboardCategory,
  type LeaderboardFailure,
  type LeaderboardResponse,
  type LeaderboardSuccess,
  type TraderEntry,
  type TradersData,
} from "./types";
import { CompetitionRules } from "./competition-rules";

const PAGE_SIZE = 10;
const SEARCH_LIMIT = 200;

const categoryLabels: Record<LeaderboardCategory, string> = {
  traders: "Trader PnL",
  creators: "Creator payouts",
  competitions: "Competitions",
};

const usd = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});

const usdc = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const percent = new Intl.NumberFormat("en-US", {
  style: "percent",
  maximumFractionDigits: 2,
});

const compact = new Intl.NumberFormat("en-US", { notation: "compact" });

function oneOf<T extends readonly string[]>(
  value: string | null,
  values: T,
  fallback: T[number],
): T[number] {
  return values.includes(value as T[number]) ? (value as T[number]) : fallback;
}

function boundedPage(value: string | null): number {
  const page = Number(value ?? "1");
  return Number.isInteger(page) && page >= 1 && page <= 500 ? page : 1;
}

function shortIdentity(value: string | null | undefined): string {
  if (!value) return "Unknown identity";
  return value.length > 14 ? `${value.slice(0, 6)}…${value.slice(-5)}` : value;
}

function safeDate(value: string | null): string {
  if (!value) return "Not scheduled";
  const date = new Date(value);
  return Number.isFinite(date.getTime())
    ? new Intl.DateTimeFormat("en-US", {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(date)
    : "Date unavailable";
}

function safeTime(value: string): string {
  const date = new Date(value);
  return Number.isFinite(date.getTime())
    ? new Intl.DateTimeFormat("en-US", {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(date)
    : "Unknown";
}

function identityLabel(
  username: string | null,
  primary: string | null,
): string {
  return username ? `@${username}` : shortIdentity(primary);
}

function VerifiedMark({ visible }: { visible: boolean }) {
  return visible ? (
    <span
      className="verified-mark"
      aria-label="Verified profile"
      title="Verified"
    >
      ✓
    </span>
  ) : null;
}

function SourceStatus({ response }: { response: LeaderboardSuccess }) {
  return (
    <div className="leaderboard-source" data-testid="leaderboard-source">
      <span className="source-dot" aria-hidden="true" />
      <span>
        <strong>{response.source.label}</strong>
        <small>Validated {safeTime(response.source.fetchedAt)}</small>
      </span>
    </div>
  );
}

function ErrorState({
  failure,
  onRetry,
}: {
  failure: LeaderboardFailure;
  onRetry: () => void;
}) {
  return (
    <section
      className="leaderboard-state leaderboard-state--error"
      role="alert"
      data-testid="leaderboard-error"
    >
      <span className="state-icon" aria-hidden="true">
        !
      </span>
      <div>
        <p className="state-kicker">{failure.source.label}</p>
        <h2>Rankings are unavailable</h2>
        <p>{failure.error.message}</p>
        <p className="state-limit">
          No cached, sample or inferred ranking rows are substituted.
        </p>
        <button className="leaderboard-button" type="button" onClick={onRetry}>
          Retry
        </button>
      </div>
    </section>
  );
}

function InvalidState({ onRetry }: { onRetry: () => void }) {
  return (
    <section
      className="leaderboard-state leaderboard-state--error"
      role="alert"
      data-testid="leaderboard-invalid"
    >
      <span className="state-icon" aria-hidden="true">
        !
      </span>
      <div>
        <p className="state-kicker">Contract validation failed</p>
        <h2>Invalid leaderboard response</h2>
        <p>
          The response did not match the validated local adapter contract, so it
          was not rendered.
        </p>
        <button className="leaderboard-button" type="button" onClick={onRetry}>
          Retry
        </button>
      </div>
    </section>
  );
}

function LoadingState() {
  return (
    <section
      className="leaderboard-loading"
      aria-busy="true"
      aria-live="polite"
      data-testid="leaderboard-loading"
    >
      <span className="leaderboard-spinner" aria-hidden="true" />
      <p>Loading validated leaderboard data…</p>
    </section>
  );
}

function EmptyState({ message }: { message: string }) {
  return (
    <section className="leaderboard-state" data-testid="leaderboard-empty">
      <span className="state-icon" aria-hidden="true">
        0
      </span>
      <div>
        <h2>No qualifying results</h2>
        <p>{message}</p>
      </div>
    </section>
  );
}

function Pagination({
  page,
  totalPages,
  onPage,
}: {
  page: number;
  totalPages: number;
  onPage: (page: number) => void;
}) {
  if (totalPages <= 1) return null;
  return (
    <nav className="leaderboard-pagination" aria-label="Leaderboard pages">
      <button
        type="button"
        disabled={page <= 1}
        onClick={() => onPage(page - 1)}
      >
        Previous
      </button>
      <span aria-live="polite">
        Page {page} of {totalPages}
      </span>
      <button
        type="button"
        disabled={page >= totalPages}
        onClick={() => onPage(page + 1)}
      >
        Next
      </button>
    </nav>
  );
}

function SearchControl({
  query,
  setQuery,
}: {
  query: string;
  setQuery: (query: string) => void;
}) {
  const [draft, setDraft] = useState(query);
  useEffect(() => setDraft(query), [query]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setQuery(draft.trim().slice(0, SEARCH_LIMIT));
  }

  return (
    <form className="leaderboard-search" role="search" onSubmit={submit}>
      <label htmlFor="leaderboard-search">Filter loaded results</label>
      <span>
        <input
          id="leaderboard-search"
          type="search"
          value={draft}
          maxLength={SEARCH_LIMIT}
          placeholder="Username or public identifier"
          onChange={(event) => setDraft(event.target.value)}
        />
        <button type="submit">Filter</button>
      </span>
      <small>
        Local filter only; it does not query an undocumented search API.
      </small>
    </form>
  );
}

function TraderRows({ entries }: { entries: TraderEntry[] }) {
  return (
    <ol className="ranking-list" aria-label="Trader rankings">
      {entries.map((entry) => (
        <li
          className="ranking-row"
          key={`${entry.rank}-${entry.walletAddress}`}
        >
          <span className="ranking-position" aria-label={`Rank ${entry.rank}`}>
            {entry.rank}
          </span>
          <span className="ranking-identity">
            <strong>
              {identityLabel(entry.username, entry.walletAddress)}
              <VerifiedMark
                visible={entry.isVerified && entry.verifiedBadgeVisible}
              />
            </strong>
            <small title={entry.walletAddress}>
              {shortIdentity(entry.walletAddress)} · {entry.positionsCount}{" "}
              positions
            </small>
          </span>
          <span className="ranking-metric">
            <strong className={entry.pnlUsd >= 0 ? "positive" : "negative"}>
              {usd.format(entry.pnlUsd)}
            </strong>
            <small>{percent.format(entry.pnlPercent / 100)} combined PnL</small>
          </span>
          <span className="ranking-facts">
            <small>Realized {usd.format(entry.realizedPnlUsd)}</small>
            <small>Unrealized {usd.format(entry.unrealizedPnlUsd)}</small>
          </span>
        </li>
      ))}
    </ol>
  );
}

function CreatorRows({ entries }: { entries: CreatorEntry[] }) {
  return (
    <ol className="ranking-list" aria-label="Creator payout rankings">
      {entries.map((entry) => {
        const primary = entry.walletAddress ?? entry.wallets[0] ?? entry.userId;
        return (
          <li className="ranking-row" key={`${entry.rank}-${primary}`}>
            <span
              className="ranking-position"
              aria-label={`Rank ${entry.rank}`}
            >
              {entry.rank}
            </span>
            <span className="ranking-identity">
              <strong>
                {identityLabel(entry.username, primary)}
                <VerifiedMark
                  visible={entry.isVerified && entry.verifiedBadgeVisible}
                />
              </strong>
              <small title={primary ?? undefined}>
                {shortIdentity(primary)}
              </small>
            </span>
            <span className="ranking-metric">
              <strong className="positive">
                {usdc.format(entry.totalPaidUsdc)}
              </strong>
              <small>confirmed USDC paid</small>
            </span>
            <span className="ranking-facts">
              <small>{compact.format(entry.payoutCount)} payouts</small>
              <small>Last paid {safeDate(entry.lastPaidAt)}</small>
            </span>
          </li>
        );
      })}
    </ol>
  );
}

function CompetitionCards({
  competitions,
  detailHref,
}: {
  competitions: CompetitionSummary[];
  detailHref: (competition: CompetitionSummary) => string;
}) {
  return (
    <ul className="competition-grid" aria-label="Competitions">
      {competitions.map((competition) => (
        <li className="competition-card" key={competition.id}>
          <div className="competition-card-heading">
            <span className={`phase phase--${competition.phase}`}>
              {competition.phase}
            </span>
            <span>{competition.kind === "group" ? "Squads" : "Traders"}</span>
          </div>
          <h2>{competition.title}</h2>
          <p>{competition.description || "No description supplied."}</p>
          <dl>
            <div>
              <dt>Prize</dt>
              <dd>{competition.prizeCopy || "Not specified"}</dd>
            </div>
            <div>
              <dt>Entries</dt>
              <dd>
                {compact.format(competition.entriesCount)} /{" "}
                {compact.format(competition.maxEntries)}
              </dd>
            </div>
            <div>
              <dt>Ends</dt>
              <dd>{safeDate(competition.endsAt)}</dd>
            </div>
          </dl>
          <CompetitionCountdown competition={competition} />
          <Link className="competition-link" href={detailHref(competition)}>
            View ranked entries
          </Link>
        </li>
      ))}
    </ul>
  );
}

function CompetitionEntryRows({ entries }: { entries: CompetitionEntry[] }) {
  return (
    <ol className="ranking-list" aria-label="Competition rankings">
      {entries.map((entry) => {
        const primary = entry.walletAddress ?? entry.participantId;
        return (
          <li className="ranking-row" key={entry.entryId}>
            <span
              className="ranking-position"
              aria-label={`Rank ${entry.rank}`}
            >
              {entry.rank}
            </span>
            <span className="ranking-identity">
              <strong>
                {identityLabel(entry.username, primary)}
                <VerifiedMark
                  visible={entry.isVerified && entry.verifiedBadgeVisible}
                />
              </strong>
              <small>
                {entry.kind === "group"
                  ? `${entry.memberCount} members`
                  : shortIdentity(primary)}
              </small>
            </span>
            <span className="ranking-metric">
              <strong className={entry.pnlUsd >= 0 ? "positive" : "negative"}>
                {usd.format(entry.pnlUsd)}
              </strong>
              <small>competition PnL</small>
            </span>
            <span className="ranking-facts">
              <small>Realized {usd.format(entry.realizedPnlUsd)}</small>
              <small>Unrealized {usd.format(entry.unrealizedPnlUsd)}</small>
            </span>
          </li>
        );
      })}
    </ol>
  );
}

export default function LeaderboardClient() {
  const searchParams = useSearchParams();
  const category = oneOf(
    searchParams.get("category"),
    leaderboardCategories,
    "traders",
  );
  const traderPeriod = oneOf(
    searchParams.get("period"),
    traderPeriods,
    "daily",
  );
  const traderSort = oneOf(searchParams.get("sort"), traderSorts, "combined");
  const creatorPeriod = oneOf(
    searchParams.get("period"),
    creatorPeriods,
    "all",
  );
  const competitionStatus = oneOf(
    searchParams.get("status"),
    competitionStatuses,
    "live",
  );
  const competitionId = searchParams.get("competition");
  const query = (searchParams.get("q") ?? "").slice(0, SEARCH_LIMIT);
  const page = boundedPage(searchParams.get("page"));
  const [response, setResponse] = useState<LeaderboardResponse | null>(null);
  const [invalid, setInvalid] = useState(false);
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  const requestSequence = useRef(0);

  const apiQuery = useMemo(() => {
    const parameters = new URLSearchParams({ category });
    if (category === "traders") {
      parameters.set("period", traderPeriod);
      parameters.set("sort", traderSort);
    } else if (category === "creators") {
      parameters.set("period", creatorPeriod);
      parameters.set("page", String(page));
    } else {
      parameters.set("status", competitionStatus);
      if (competitionId) parameters.set("id", competitionId);
    }
    return parameters.toString();
  }, [
    category,
    competitionId,
    competitionStatus,
    creatorPeriod,
    page,
    traderPeriod,
    traderSort,
  ]);

  useEffect(() => {
    const controller = new AbortController();
    const sequence = ++requestSequence.current;
    setLoading(true);
    setInvalid(false);
    setResponse(null);

    fetch(`/api/leaderboard?${apiQuery}`, {
      method: "GET",
      headers: { Accept: "application/json" },
      signal: controller.signal,
    })
      .then(async (result) => {
        const body: unknown = await result.json();
        return parseLeaderboardResponse(body);
      })
      .then((nextResponse) => {
        if (sequence === requestSequence.current) setResponse(nextResponse);
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted || sequence !== requestSequence.current)
          return;
        if (
          error instanceof Error &&
          error.message.includes("invalid response")
        ) {
          setInvalid(true);
          return;
        }
        setResponse({
          ok: false,
          error: {
            code: "NETWORK_FAILURE",
            message: "The local leaderboard adapter could not be reached.",
            retryable: true,
          },
          source: { mode: "offline", label: "Local adapter unavailable" },
        });
      })
      .finally(() => {
        if (sequence === requestSequence.current) setLoading(false);
      });

    return () => controller.abort();
  }, [apiQuery, retry]);

  const updateQuery = useCallback(
    (changes: Record<string, string | null>, resetPage = true) => {
      const next = new URLSearchParams(window.location.search);
      for (const [name, value] of Object.entries(changes)) {
        if (value) next.set(name, value);
        else next.delete(name);
      }
      if (resetPage && !Object.hasOwn(changes, "page")) next.delete("page");
      const serialized = next.toString();
      // Commit the URL synchronously so a second control change merges with it
      // even before React renders. Next syncs native history with useSearchParams.
      window.history.pushState(
        null,
        "",
        serialized ? `/leaderboard?${serialized}` : "/leaderboard",
      );
    },
    [],
  );

  const setSearch = (nextQuery: string) =>
    updateQuery({ q: nextQuery || null }, true);
  const setPage = (nextPage: number) =>
    updateQuery({ page: String(nextPage) }, false);

  const lowerQuery = query.toLocaleLowerCase();

  let content: React.ReactNode = null;
  if (loading) {
    content = <LoadingState />;
  } else if (invalid) {
    content = <InvalidState onRetry={() => setRetry((value) => value + 1)} />;
  } else if (response && !response.ok) {
    content = (
      <ErrorState
        failure={response}
        onRetry={() => setRetry((value) => value + 1)}
      />
    );
  } else if (response?.ok && response.data.kind === "traders") {
    const data: TradersData = response.data;
    const filtered = data.entries.filter((entry) =>
      [entry.username, entry.walletAddress, entry.xUsername, entry.userId]
        .filter(Boolean)
        .some((value) => value!.toLocaleLowerCase().includes(lowerQuery)),
    );
    const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
    const visiblePage = Math.min(page, totalPages);
    const entries = filtered.slice(
      (visiblePage - 1) * PAGE_SIZE,
      visiblePage * PAGE_SIZE,
    );
    content = entries.length ? (
      <>
        <div className="leaderboard-summary">
          <span>{data.periodLabel}</span>
          <span>{filtered.length} validated traders</span>
        </div>
        <TraderRows entries={entries} />
        <Pagination
          page={visiblePage}
          totalPages={totalPages}
          onPage={setPage}
        />
      </>
    ) : (
      <EmptyState message="No loaded trader identity matches this local filter." />
    );
  } else if (response?.ok && response.data.kind === "creators") {
    const data: CreatorsData = response.data;
    const entries = data.entries.filter((entry) =>
      [entry.username, entry.userId, entry.walletAddress, ...entry.wallets]
        .filter(Boolean)
        .some((value) => value!.toLocaleLowerCase().includes(lowerQuery)),
    );
    const { totalPages, outOfRange } = creatorPagination(data);
    content = (
      <>
        <div className="leaderboard-summary">
          <span>{compact.format(data.totalEarners)} confirmed earners</span>
          {data.totalEarners > CREATOR_LEADERBOARD_LIMIT ? (
            <span>Top {CREATOR_LEADERBOARD_LIMIT} available</span>
          ) : null}
          <span>
            Generated{" "}
            {data.generatedAt ? safeTime(data.generatedAt) : "unknown"}
          </span>
        </div>
        {outOfRange ? (
          <>
            <EmptyState
              message={`Page ${data.page} is outside the available payout board (pages 1–${totalPages}).`}
            />
            <button
              className="leaderboard-button"
              type="button"
              onClick={() => setPage(1)}
            >
              Back to first payout page
            </button>
          </>
        ) : (
          <>
            {entries.length ? (
              <CreatorRows entries={entries} />
            ) : (
              <EmptyState message="No creator on this loaded page matches the local filter." />
            )}
            <Pagination
              page={data.page}
              totalPages={totalPages}
              onPage={setPage}
            />
          </>
        )}
      </>
    );
  } else if (response?.ok && response.data.kind === "competitions") {
    const data: CompetitionsData = response.data;
    const bucket = data[competitionStatus].filter((competition) =>
      [competition.title, competition.description, competition.slug]
        .filter(Boolean)
        .some((value) => value.toLocaleLowerCase().includes(lowerQuery)),
    );
    const totalPages = Math.max(1, Math.ceil(bucket.length / 6));
    const visiblePage = Math.min(page, totalPages);
    const competitions = bucket.slice((visiblePage - 1) * 6, visiblePage * 6);
    content = competitions.length ? (
      <>
        <div className="leaderboard-summary">
          <span>
            {bucket.length} {competitionStatus} competitions
          </span>
          <span>Captured list ordering preserved</span>
        </div>
        <CompetitionCards
          competitions={competitions}
          detailHref={(competition) => {
            const next = new URLSearchParams(searchParams.toString());
            next.set("competition", competition.slug);
            next.delete("page");
            return `/leaderboard?${next.toString()}`;
          }}
        />
        <Pagination
          page={visiblePage}
          totalPages={totalPages}
          onPage={setPage}
        />
      </>
    ) : (
      <EmptyState
        message={`No ${competitionStatus} competition matches this local filter.`}
      />
    );
  } else if (response?.ok && response.data.kind === "competition-detail") {
    const data: CompetitionDetailData = response.data;
    const filtered = data.entries.filter((entry) =>
      [entry.username, entry.participantId, entry.walletAddress]
        .filter(Boolean)
        .some((value) => value!.toLocaleLowerCase().includes(lowerQuery)),
    );
    const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
    const visiblePage = Math.min(page, totalPages);
    const entries = filtered.slice(
      (visiblePage - 1) * PAGE_SIZE,
      visiblePage * PAGE_SIZE,
    );
    content = (
      <>
        <div className="competition-detail-heading">
          <button
            className="text-button"
            type="button"
            onClick={() =>
              updateQuery({ competition: null, page: null }, false)
            }
          >
            ← Back to competitions
          </button>
          <span className={`phase phase--${data.competition.phase}`}>
            {data.competition.phase}
          </span>
          <h2>{data.competition.title}</h2>
          <p>{data.competition.description}</p>
          <CompetitionRules key={data.competition.id} competition={data.competition} />
          <dl>
            <div>
              <dt>Ranked entries</dt>
              <dd>{compact.format(data.totalRanked)}</dd>
            </div>
            <div>
              <dt>Prize</dt>
              <dd>{data.competition.prizeCopy || "Not specified"}</dd>
            </div>
            <div>
              <dt>Result</dt>
              <dd>{data.isFinal ? "Final" : "In progress"}</dd>
            </div>
          </dl>
        </div>
        {entries.length ? (
          <>
            <CompetitionEntryRows entries={entries} />
            <Pagination
              page={visiblePage}
              totalPages={totalPages}
              onPage={setPage}
            />
          </>
        ) : (
          <EmptyState message="No ranked competition entry matches this local filter." />
        )}
      </>
    );
  }

  return (
    <div className="leaderboard-app">
      <nav
        className="leaderboard-categories"
        aria-label="Leaderboard categories"
      >
        {leaderboardCategories.map((item) => (
          <Link
            key={item}
            href={`/leaderboard?category=${item}`}
            aria-current={category === item ? "page" : undefined}
          >
            {categoryLabels[item]}
          </Link>
        ))}
      </nav>

      <section
        className="leaderboard-toolbar"
        aria-label="Leaderboard controls"
      >
        {category === "traders" ? (
          <>
            <label>
              Period
              <select
                aria-label="Trader period"
                value={traderPeriod}
                onChange={(event) =>
                  updateQuery({ period: event.target.value }, true)
                }
              >
                {traderPeriods.map((item) => (
                  <option key={item} value={item}>
                    {item[0].toUpperCase() + item.slice(1)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Sort
              <select
                aria-label="Trader sort"
                value={traderSort}
                onChange={(event) =>
                  updateQuery({ sort: event.target.value }, true)
                }
              >
                {traderSorts.map((item) => (
                  <option key={item} value={item}>
                    {item[0].toUpperCase() + item.slice(1)} PnL
                  </option>
                ))}
              </select>
            </label>
          </>
        ) : null}
        {category === "creators" ? (
          <label>
            Payout period
            <select
              aria-label="Creator payout period"
              value={creatorPeriod}
              onChange={(event) =>
                updateQuery({ period: event.target.value }, true)
              }
            >
              {creatorPeriods.map((item) => (
                <option key={item} value={item}>
                  {item === "all" ? "All time" : item}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        {category === "competitions" && !competitionId ? (
          <label>
            Status
            <select
              aria-label="Competition status"
              value={competitionStatus}
              onChange={(event) =>
                updateQuery({ status: event.target.value }, true)
              }
            >
              {competitionStatuses.map((item: CompetitionStatus) => (
                <option key={item} value={item}>
                  {item[0].toUpperCase() + item.slice(1)}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        <SearchControl query={query} setQuery={setSearch} />
      </section>

      {response?.ok ? <SourceStatus response={response} /> : null}
      <div className="leaderboard-results">{content}</div>
      <p className="leaderboard-disclosure">
        Data source: documented developer operations. The website origin was
        observed in captured bundles but returned HTTP 403 during bounded local
        qualification; no website/API equivalence is claimed.
      </p>
    </div>
  );
}
