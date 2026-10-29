"use client";

import { useRouter, useSearchParams } from "next/navigation";
import {
  type FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  useTransition,
} from "react";
import type {
  ArchivedBounty,
  GoPageResult,
  GoQuery,
  GoSortField,
  GoSortOrder,
  PublicPhase,
} from "./go-data";

const phases: ReadonlyArray<{ value: GoQuery["status"]; label: string }> = [
  { value: "ALL", label: "All" },
  { value: "OPEN", label: "Open at capture" },
  { value: "PENDING_RESOLUTION", label: "Pending dispute" },
  { value: "IN_DISPUTE_PERIOD", label: "In dispute" },
  { value: "CLOSED", label: "Closed" },
];

const sortOptions: ReadonlyArray<{ value: GoSortField; label: string }> = [
  { value: "createdAt", label: "Recently created" },
  { value: "rewardTotalUsd", label: "Reward value at capture" },
  { value: "expiresAt", label: "Expiration" },
  { value: "submissionCount", label: "Submissions" },
];

const solMint = "So11111111111111111111111111111111111111112";

function shortAddress(value: string): string {
  return `${value.slice(0, 5)}…${value.slice(-5)}`;
}

function formatAtomicAmount(
  amountAtomic: string | undefined,
  decimals: number | undefined,
): string | undefined {
  if (
    amountAtomic === undefined ||
    decimals === undefined ||
    !/^\d{1,80}$/u.test(amountAtomic) ||
    !Number.isInteger(decimals) ||
    decimals < 0 ||
    decimals > 18
  )
    return undefined;
  const value = BigInt(amountAtomic);
  if (decimals === 0) return value.toString();
  const divisor = 10n ** BigInt(decimals);
  const fraction = (value % divisor)
    .toString()
    .padStart(decimals, "0")
    .replace(/0+$/u, "");
  return fraction
    ? `${value / divisor}.${fraction}`
    : (value / divisor).toString();
}

function mintLabel(mint: string): string {
  return mint === solMint ? "SOL" : `${mint.slice(0, 4)}…${mint.slice(-4)}`;
}

function phaseLabel(phase: ArchivedBounty["phaseAtCapture"]): string {
  return (
    phases.find((entry) => entry.value === phase)?.label ??
    phase.replaceAll("_", " ")
  );
}

function isPageResult(value: unknown): value is GoPageResult {
  if (!value || typeof value !== "object") return false;
  const page = value as Partial<GoPageResult>;
  return (
    page.source === "archived-go-html" &&
    typeof page.capturedAt === "string" &&
    typeof page.refreshedAt === "string" &&
    Number.isSafeInteger(page.total) &&
    Number.isSafeInteger(page.offset) &&
    Array.isArray(page.items) &&
    page.items.every(
      (item) =>
        item !== null &&
        typeof item === "object" &&
        typeof item.taskId === "string" &&
        typeof item.title === "string" &&
        typeof item.creatorAddress === "string" &&
        Array.isArray(item.rewardLegs),
    )
  );
}

function BountyDetail({
  bounty,
  onClose,
}: {
  bounty?: ArchivedBounty;
  onClose: () => void;
}) {
  if (!bounty) return null;
  return (
    <aside
      className="go-detail"
      aria-labelledby="go-detail-title"
      data-testid="go-bounty-detail"
    >
      <div className="go-detail-heading">
        <div>
          <p className="go-kicker">Archived detail</p>
          <h2 id="go-detail-title">{bounty.title}</h2>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close bounty detail"
        >
          Close
        </button>
      </div>
      <p className="go-body">{bounty.bodyText}</p>
      <dl className="go-facts">
        <div>
          <dt>Status at capture</dt>
          <dd>{phaseLabel(bounty.phaseAtCapture)}</dd>
        </div>
        <div>
          <dt>Creator</dt>
          <dd title={bounty.creatorAddress}>
            {shortAddress(bounty.creatorAddress)}
          </dd>
        </div>
        <div>
          <dt>Submissions</dt>
          <dd>{bounty.submissionCount.toLocaleString("en-US")}</dd>
        </div>
        <div>
          <dt>Expires</dt>
          <dd>
            {bounty.expiresAt
              ? new Date(bounty.expiresAt).toLocaleDateString("en-US")
              : "Not recorded"}
          </dd>
        </div>
      </dl>
      <section
        className="go-unavailable"
        aria-label="Unsupported bounty actions"
      >
        <strong>Account actions unavailable</strong>
        <p>
          Funding, submissions, moderation and payouts require unqualified
          authenticated services and remain disabled.
        </p>
      </section>
    </aside>
  );
}

export default function GoExplorer({
  initialPage,
  initialQuery,
  ignoredInvalidState,
}: {
  initialPage: GoPageResult;
  initialQuery: GoQuery;
  ignoredInvalidState: boolean;
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [page, setPage] = useState(initialPage);
  const [draftQuery, setDraftQuery] = useState(initialQuery.q);
  const [error, setError] = useState<string>();
  const [isLoading, setIsLoading] = useState(false);
  const [retryVersion, setRetryVersion] = useState(0);
  const [isPending, startTransition] = useTransition();
  const requestSequence = useRef(0);
  const pendingQuery = useRef<string | null>(null);
  const initialKey = useRef<string | undefined>(undefined);
  const cardRefs = useRef(new Map<string, HTMLButtonElement>());

  const rawQ = searchParams.get("q") ?? "";
  const q = rawQ.length <= 256 ? rawQ : initialQuery.q;
  const rawStatus = searchParams.get("status") ?? "ALL";
  const status = phases.some((phase) => phase.value === rawStatus)
    ? (rawStatus as GoQuery["status"])
    : initialQuery.status;
  const rawSort = searchParams.get("sort") ?? "createdAt";
  const sort = sortOptions.some((option) => option.value === rawSort)
    ? (rawSort as GoSortField)
    : initialQuery.sort;
  const rawOrder = searchParams.get("order") ?? "desc";
  const order: GoSortOrder =
    rawOrder === "asc" || rawOrder === "desc" ? rawOrder : initialQuery.order;
  const rawCursor = searchParams.get("cursor") ?? undefined;
  const cursor =
    rawCursor &&
    /^c\d{1,4}$/u.test(rawCursor) &&
    Number.parseInt(rawCursor.slice(1), 10) % 24 === 0
      ? rawCursor
      : initialQuery.cursor;
  const rawTask = searchParams.get("task") ?? undefined;
  const selectedTask =
    rawTask &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/iu.test(
      rawTask,
    )
      ? rawTask
      : initialQuery.task;
  const requestKey = `${q}\0${status}\0${sort}\0${order}\0${cursor ?? ""}`;

  const selected = useMemo(
    () => page.items.find((item) => item.taskId === selectedTask),
    [page.items, selectedTask],
  );

  const navigate = useCallback(
    (changes: Record<string, string | null>, replace = false) => {
      // Compose actions against the last requested query until navigation settles.
      const parameters = new URLSearchParams(pendingQuery.current ?? "");
      if (pendingQuery.current === null) {
        if (q) parameters.set("q", q);
        if (status !== "ALL") parameters.set("status", status);
        if (sort !== "createdAt") parameters.set("sort", sort);
        if (order !== "desc") parameters.set("order", order);
        if (cursor && cursor !== "c0") parameters.set("cursor", cursor);
        if (selectedTask) parameters.set("task", selectedTask);
      }
      for (const [key, value] of Object.entries(changes)) {
        if (
          !value ||
          (key === "status" && value === "ALL") ||
          (key === "sort" && value === "createdAt") ||
          (key === "order" && value === "desc") ||
          (key === "cursor" && value === "c0")
        )
          parameters.delete(key);
        else parameters.set(key, value);
      }
      pendingQuery.current = parameters.toString();
      const target = parameters.size ? `/go?${parameters}` : "/go";
      startTransition(() =>
        replace
          ? router.replace(target, { scroll: false })
          : router.push(target, { scroll: false }),
      );
    },
    [cursor, order, q, router, selectedTask, sort, status],
  );

  useEffect(() => {
    // An earlier response must not replace a newer pending action.
    if (!isPending) pendingQuery.current = null;
  }, [isPending, searchParams]);

  useEffect(() => {
    const onPopState = () => {
      pendingQuery.current = null;
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => setDraftQuery(q), [q]);

  useEffect(() => {
    if (initialKey.current === undefined) {
      initialKey.current = requestKey;
      return;
    }
    const controller = new AbortController();
    const sequence = ++requestSequence.current;
    const parameters = new URLSearchParams();
    if (q) parameters.set("q", q);
    if (status !== "ALL") parameters.set("status", status);
    if (sort !== "createdAt") parameters.set("sort", sort);
    if (order !== "desc") parameters.set("order", order);
    if (cursor) parameters.set("cursor", cursor);
    setError(undefined);
    setIsLoading(true);
    fetch(`/api/go-bounties?${parameters}`, {
      signal: controller.signal,
      headers: { Accept: "application/json" },
    })
      .then(async (response) => {
        if (!response.ok)
          throw new Error(`Archive request failed (${response.status})`);
        const value: unknown = await response.json();
        if (!isPageResult(value))
          throw new Error("Archive response failed validation");
        return value;
      })
      .then((value) => {
        if (sequence === requestSequence.current) {
          setPage(value);
          setIsLoading(false);
        }
      })
      .catch((cause: unknown) => {
        if (cause instanceof DOMException && cause.name === "AbortError")
          return;
        if (sequence === requestSequence.current) {
          setError(
            cause instanceof Error ? cause.message : "Archive request failed",
          );
          setIsLoading(false);
        }
      });
    return () => controller.abort();
  }, [cursor, order, q, requestKey, retryVersion, sort, status]);

  const closeDetail = useCallback(() => {
    const task = selectedTask;
    navigate({ task: null });
    if (task) requestAnimationFrame(() => cardRefs.current.get(task)?.focus());
  }, [navigate, selectedTask]);

  useEffect(() => {
    if (!selectedTask) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !event.defaultPrevented) {
        event.preventDefault();
        closeDetail();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [closeDetail, selectedTask]);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    navigate({ q: draftQuery.trim() || null, cursor: null, task: null });
  }

  return (
    <div
      className="go-workspace"
      aria-busy={isPending || isLoading || undefined}
    >
      {ignoredInvalidState ? (
        <p className="go-query-warning" role="status">
          Unsupported URL filters were ignored safely.
        </p>
      ) : null}
      <form
        className="go-controls"
        role="search"
        aria-label="Search archived GO bounties"
        onSubmit={submitSearch}
      >
        <div className="go-search-field">
          <label htmlFor="go-search">Search archived bounties</label>
          <input
            id="go-search"
            type="search"
            maxLength={256}
            autoComplete="off"
            value={draftQuery}
            placeholder="Title, description, creator or task ID"
            onChange={(event) => setDraftQuery(event.target.value)}
          />
        </div>
        <button className="go-primary" type="submit">
          Search
        </button>
        <button
          className="go-secondary"
          type="button"
          onClick={() => {
            setDraftQuery("");
            navigate({
              q: null,
              status: null,
              sort: null,
              order: null,
              cursor: null,
              task: null,
            });
          }}
        >
          Reset
        </button>
        <label className="go-select">
          Status at capture
          <select
            value={status}
            onChange={(event) =>
              navigate({ status: event.target.value, cursor: null, task: null })
            }
          >
            {phases.map((phase) => (
              <option key={phase.value} value={phase.value}>
                {phase.label}
              </option>
            ))}
          </select>
        </label>
        <label className="go-select">
          Sort by
          <select
            value={sort}
            onChange={(event) =>
              navigate({ sort: event.target.value, cursor: null, task: null })
            }
          >
            {sortOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label className="go-select">
          Direction
          <select
            value={order}
            onChange={(event) =>
              navigate({ order: event.target.value, cursor: null, task: null })
            }
          >
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </label>
      </form>

      {isLoading ? (
        <p className="go-fetching" role="status" aria-live="polite">
          Updating archived results…
        </p>
      ) : null}

      {error ? (
        <section
          className="go-failure"
          role="alert"
          data-testid="go-request-error"
        >
          <p className="go-kicker">Local archive unavailable</p>
          <h2>Could not load this result page</h2>
          <p>{error}. The app did not fall back to a production service.</p>
          <button
            type="button"
            className="go-primary"
            onClick={() => setRetryVersion((value) => value + 1)}
          >
            Retry
          </button>
        </section>
      ) : (
        <>
          <div className="go-results-heading" aria-live="polite">
            <div>
              <p className="go-kicker">Historical results</p>
              <h2>
                {page.total} archived {page.total === 1 ? "bounty" : "bounties"}
              </h2>
            </div>
            <p>
              Showing {page.items.length ? page.offset + 1 : 0}–
              {page.offset + page.items.length}
            </p>
          </div>
          {selectedTask ? (
            selected ? (
              <BountyDetail bounty={selected} onClose={closeDetail} />
            ) : (
              <section className="go-failure" role="alert">
                <h2>Archived bounty not found</h2>
                <p>The selected task is not on this result page.</p>
                <button
                  className="go-secondary"
                  type="button"
                  onClick={closeDetail}
                >
                  Close detail
                </button>
              </section>
            )
          ) : null}
          {page.items.length ? (
            <div className="go-list" aria-label="Archived bounty results">
              {page.items.map((bounty) => (
                <article
                  className="go-card"
                  key={bounty.taskId}
                  data-testid="go-bounty-card"
                >
                  <div className="go-card-heading">
                    <span
                      className={`go-phase go-phase--${bounty.phaseAtCapture.toLowerCase()}`}
                    >
                      {phaseLabel(bounty.phaseAtCapture)}
                    </span>
                    <time dateTime={bounty.createdAt}>
                      {new Date(bounty.createdAt).toLocaleDateString("en-US")}
                    </time>
                  </div>
                  <h3>{bounty.title}</h3>
                  <p className="go-card-copy">{bounty.bodyText}</p>
                  <dl className="go-card-facts">
                    <div>
                      <dt>Reward</dt>
                      <dd>
                        {bounty.rewardLegs.length
                          ? bounty.rewardLegs
                              .map((leg) => {
                                const amount = formatAtomicAmount(
                                  leg.amountAtomic,
                                  leg.decimalsSnapshot,
                                );
                                return amount
                                  ? `${amount} ${mintLabel(leg.mintAddress)}`
                                  : `Amount unavailable (${mintLabel(leg.mintAddress)})`;
                              })
                              .join(" + ")
                          : "Not recorded"}
                      </dd>
                    </div>
                    <div>
                      <dt>Submissions</dt>
                      <dd>{bounty.submissionCount.toLocaleString("en-US")}</dd>
                    </div>
                    <div>
                      <dt>Creator</dt>
                      <dd title={bounty.creatorAddress}>
                        {shortAddress(bounty.creatorAddress)}
                      </dd>
                    </div>
                  </dl>
                  <button
                    ref={(node) => {
                      if (node) cardRefs.current.set(bounty.taskId, node);
                      else cardRefs.current.delete(bounty.taskId);
                    }}
                    className="go-primary"
                    type="button"
                    onClick={() => navigate({ task: bounty.taskId })}
                    aria-label={`Inspect archived bounty ${bounty.title}`}
                  >
                    Inspect details
                  </button>
                </article>
              ))}
            </div>
          ) : (
            <section
              className="go-empty"
              role="status"
              data-testid="go-empty-results"
            >
              <p className="go-kicker">No archived matches</p>
              <h2>Try a different search or filter</h2>
              <p>
                This empty result describes only the authenticated historical
                snapshot.
              </p>
            </section>
          )}
          <nav className="go-pagination" aria-label="Archived bounty pages">
            <button
              className="go-secondary"
              type="button"
              disabled={!page.previousCursor}
              onClick={() =>
                navigate({ cursor: page.previousCursor ?? null, task: null })
              }
            >
              Previous page
            </button>
            <span>Page {Math.floor(page.offset / 24) + 1}</span>
            <button
              className="go-secondary"
              type="button"
              disabled={!page.nextCursor}
              onClick={() =>
                navigate({ cursor: page.nextCursor ?? null, task: null })
              }
            >
              Next page
            </button>
          </nav>
        </>
      )}
    </div>
  );
}
