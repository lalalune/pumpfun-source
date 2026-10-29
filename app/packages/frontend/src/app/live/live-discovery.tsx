"use client";

import { useRouter, useSearchParams } from "next/navigation";
import {
  type FormEvent,
  type KeyboardEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import type { ArchivedStream } from "./live-data";
import {
  filterArchivedStreams,
  paginateArchivedStreams,
  type LiveSort,
} from "./live-filter";

type SectionId = "most-viewers" | "other-sections";

const sections: ReadonlyArray<{ id: SectionId; label: string }> = [
  { id: "most-viewers", label: "Most viewers" },
  { id: "other-sections", label: "Other sections" },
];

function shortAddress(value: string): string {
  return `${value.slice(0, 5)}…${value.slice(-5)}`;
}

function StreamPlaceholder({ stream }: { stream: ArchivedStream }) {
  return (
    <span className="live-card-art" aria-hidden="true">
      <span>{stream.symbol.slice(0, 3)}</span>
      <small>Archived preview withheld</small>
    </span>
  );
}

function PlaybackPanel({
  selected,
  invalidSelection,
  controlsReady,
  onClose,
}: {
  selected?: ArchivedStream;
  invalidSelection: boolean;
  controlsReady: boolean;
  onClose: () => void;
}) {
  if (!selected && !invalidSelection) {
    return (
      <aside className="playback-panel" aria-labelledby="playback-heading">
        <p className="playback-kicker">Playback state</p>
        <h2 id="playback-heading">No archived stream selected</h2>
        <p>
          Select a captured card to inspect its read-only metadata. No player or
          production media session starts here.
        </p>
      </aside>
    );
  }

  if (!controlsReady) {
    return (
      <aside
        className="playback-panel"
        role="status"
        aria-live="polite"
        data-testid="stream-detail-loading"
      >
        Loading archived details…
      </aside>
    );
  }

  if (invalidSelection) {
    return (
      <aside
        className="playback-panel playback-panel--warning"
        aria-labelledby="playback-heading"
        data-testid="invalid-stream-selection"
      >
        <div className="playback-heading-row">
          <div>
            <p className="playback-kicker">Invalid metadata</p>
            <h2 id="playback-heading">Selection unavailable</h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close stream detail"
          >
            Close
          </button>
        </div>
        <p>
          The URL does not identify a record in the authenticated local
          snapshot. Nothing was fetched from a production service.
        </p>
      </aside>
    );
  }

  return (
    <aside
      className="playback-panel playback-panel--selected"
      aria-labelledby="playback-heading"
      data-testid="playback-unavailable"
    >
      <div className="playback-heading-row">
        <div>
          <p className="playback-kicker">Playback unavailable</p>
          <h2 id="playback-heading">{selected?.title}</h2>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close stream detail"
        >
          Close
        </button>
      </div>
      <div
        className="playback-stage"
        aria-label="Archived playback unavailable"
      >
        <span aria-hidden="true">▶</span>
        <strong>No media session was started</strong>
        <small>
          Captured playlist metadata is intentionally not exposed or requested.
        </small>
      </div>
      <dl className="playback-facts">
        <div>
          <dt>Symbol</dt>
          <dd>{selected?.symbol}</dd>
        </div>
        <div>
          <dt>Viewers at capture</dt>
          <dd>{selected?.viewerCountAtCapture.toLocaleString("en-US")}</dd>
        </div>
        <div>
          <dt>Creator address</dt>
          <dd title={selected?.creatorAddress}>
            {selected ? shortAddress(selected.creatorAddress) : ""}
          </dd>
        </div>
      </dl>
      <p className="playback-boundary">
        This record was marked live in the archived response. That does not mean
        the broadcast is live now.
      </p>
    </aside>
  );
}

export default function LiveDiscovery({
  streams,
}: {
  streams: ArchivedStream[];
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pendingQuery = useRef(searchParams.toString());
  const section: SectionId =
    searchParams.get("section") === "other-sections"
      ? "other-sections"
      : "most-viewers";
  const sortValue = searchParams.get("sort");
  const sort: LiveSort =
    sortValue === "title" || sortValue === "viewers" ? sortValue : "captured";
  const query = searchParams.get("q") ?? "";
  const selectedId = searchParams.get("stream");
  const [draftQuery, setDraftQuery] = useState(query);
  const [controlsReady, setControlsReady] = useState(false);
  const pendingClear = useRef(false);
  const cardRefs = useRef(new Map<string, HTMLButtonElement>());
  const searchRef = useRef<HTMLInputElement>(null);
  const selected = streams.find((stream) => stream.id === selectedId);
  const invalidSelection = selectedId !== null && selected === undefined;
  const results = useMemo(
    () => filterArchivedStreams(streams, query, sort),
    [query, sort, streams],
  );

  const page = paginateArchivedStreams(results, searchParams.getAll("page"));

  useEffect(() => {
    // A delayed clear must not overwrite a draft typed after the click.
    const completedClear = pendingClear.current && query === "";
    pendingClear.current = false;
    if (!completedClear) setDraftQuery(query);
  }, [query]);

  useEffect(() => {
    const onPopState = () => {
      pendingClear.current = false;
    };
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  useEffect(() => {
    pendingQuery.current = searchParams.toString();
  }, [searchParams]);

  const navigate = useCallback(
    (changes: Record<string, string | null>, replace = false) => {
      // Compose rapid actions before the router commits its previous URL.
      const parameters = new URLSearchParams(pendingQuery.current);
      for (const [key, value] of Object.entries(changes)) {
        if (value === null || value === "") parameters.delete(key);
        else parameters.set(key, value);
      }
      pendingQuery.current = parameters.toString();
      const target = parameters.size ? `/live?${parameters}` : "/live";
      if (replace) router.replace(target, { scroll: false });
      else router.push(target, { scroll: false });
    },
    [router],
  );

  const closeSelection = useCallback(() => {
    const previous = selectedId;
    navigate({ stream: null });
    requestAnimationFrame(() => {
      const target =
        (previous ? cardRefs.current.get(previous) : undefined) ??
        searchRef.current ??
        document.getElementById(`live-section-${section}`);
      target?.focus();
    });
  }, [navigate, selectedId, section]);

  useEffect(() => {
    if (selectedId === null) {
      setControlsReady(true);
      return;
    }
    const closeOnEscape = (event: globalThis.KeyboardEvent) => {
      // A modal (for example, shell settings/search) owns Escape before the
      // nonmodal metadata panel. Native dialog cancellation follows keydown;
      // defaultPrevented alone therefore cannot identify that ownership.
      const modalOwnsEvent =
        event.target instanceof Element &&
        event.target.closest(
          'dialog[open], [role="dialog"][aria-modal="true"]',
        );
      if (
        event.key === "Escape" &&
        !event.defaultPrevented &&
        !modalOwnsEvent
      ) {
        event.preventDefault();
        closeSelection();
      }
    };
    window.addEventListener("keydown", closeOnEscape);
    // A direct visit can paint its archived selection before passive effects.
    // Expose the detail only after its advertised dismissal controls work.
    setControlsReady(true);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [closeSelection, selectedId]);

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    pendingClear.current = false;
    navigate({ q: draftQuery.trim() || null, stream: null, page: null });
  }

  function selectSection(next: SectionId) {
    navigate({
      section: next === "most-viewers" ? null : next,
      stream: null,
      page: null,
    });
  }

  function handleSectionKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    const current = sections.findIndex(({ id }) => id === section);
    let next = current;
    if (event.key === "ArrowRight" || event.key === "ArrowDown")
      next = current + 1;
    else if (event.key === "ArrowLeft" || event.key === "ArrowUp")
      next = current - 1;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = sections.length - 1;
    else return;
    event.preventDefault();
    const target = sections[(next + sections.length) % sections.length];
    selectSection(target.id);
    requestAnimationFrame(() =>
      document.getElementById(`live-section-${target.id}`)?.focus(),
    );
  }

  return (
    <div className="live-workspace">
      <nav className="live-sections" aria-label="Live discovery sections">
        <div role="tablist" aria-label="Captured Live sections">
          {sections.map((item) => (
            <button
              id={`live-section-${item.id}`}
              key={item.id}
              type="button"
              role="tab"
              aria-controls="live-section-panel"
              aria-selected={section === item.id}
              tabIndex={section === item.id ? 0 : -1}
              onClick={() => selectSection(item.id)}
              onKeyDown={handleSectionKeyDown}
            >
              {item.label}
            </button>
          ))}
        </div>
      </nav>

      <div className="live-layout">
        <section
          id="live-section-panel"
          className="live-discovery-panel"
          role="tabpanel"
          aria-labelledby={`live-section-${section}`}
        >
          {section === "other-sections" ? (
            <div
              className="live-empty"
              data-testid="other-sections-unavailable"
            >
              <p className="playback-kicker">Evidence boundary</p>
              <h2>Other section listings are unavailable</h2>
              <p>
                This adapter validates only the captured Most viewers section.
                Other section payloads are not mapped or exposed by this local
                view.
              </p>
              <button
                type="button"
                onClick={() => selectSection("most-viewers")}
              >
                Return to captured cards
              </button>
            </div>
          ) : (
            <>
              <form
                className="live-controls"
                role="search"
                aria-label="Search the archived Live snapshot"
                onSubmit={submitSearch}
              >
                <label htmlFor="live-search">Search captured streams</label>
                <div className="live-control-row">
                  <input
                    id="live-search"
                    ref={searchRef}
                    type="search"
                    value={draftQuery}
                    placeholder="Title, symbol, creator or mint"
                    autoComplete="off"
                    onChange={(event) => setDraftQuery(event.target.value)}
                  />
                  {draftQuery ? (
                    <button
                      type="button"
                      className="live-secondary-button"
                      onClick={() => {
                        pendingClear.current = query !== "";
                        setDraftQuery("");
                        navigate({ q: null, stream: null, page: null });
                      }}
                    >
                      Clear
                    </button>
                  ) : null}
                  <button type="submit" className="live-primary-button">
                    Search
                  </button>
                </div>
                <label htmlFor="live-sort">Sort captured cards</label>
                <select
                  id="live-sort"
                  value={sort}
                  onChange={(event) =>
                    navigate({
                      sort:
                        event.target.value === "captured"
                          ? null
                          : event.target.value,
                      stream: null,
                      page: null,
                    })
                  }
                >
                  <option value="captured">Captured order</option>
                  <option value="viewers">Viewers at capture</option>
                  <option value="title">Title</option>
                </select>
              </form>

              <div className="live-results-heading" aria-live="polite">
                <div>
                  <p className="playback-kicker">Historical snapshot</p>
                  <h2>
                    {results.length} captured{" "}
                    {results.length === 1 ? "record" : "records"}
                  </h2>
                </div>
                {query ? <p>Query: {query}</p> : null}
              </div>

              {!page.valid ? (
                <div
                  className="live-empty"
                  data-testid="live-invalid-page"
                  role="alert"
                >
                  <h2>Archive page unavailable</h2>
                  <p>
                    Choose a single page from 1 to {page.pageCount} for these
                    results. No replacement page or production data was loaded.
                  </p>
                  <button
                    type="button"
                    onClick={() => navigate({ page: null, stream: null })}
                  >
                    Return to first page
                  </button>
                </div>
              ) : results.length > 0 ? (
                <>
                  <nav
                    className="live-pagination"
                    aria-label="Archived stream pages"
                  >
                    <p aria-live="polite">
                      Showing {page.start}–{page.end} of {page.total} captured
                      records
                    </p>
                    <div>
                      <button
                        type="button"
                        disabled={page.page === 1}
                        onClick={() =>
                          navigate({
                            page:
                              page.page === 2 ? null : String(page.page - 1),
                            stream: null,
                          })
                        }
                      >
                        Previous page
                      </button>
                      <span aria-current="page">
                        Page {page.page} of {page.pageCount}
                      </span>
                      <button
                        type="button"
                        disabled={page.page === page.pageCount}
                        onClick={() =>
                          navigate({
                            page: String(page.page + 1),
                            stream: null,
                          })
                        }
                      >
                        Next page
                      </button>
                    </div>
                  </nav>
                  <div
                    className="stream-grid"
                    aria-label="Archived stream cards"
                  >
                    {page.streams.map((stream) => (
                      <article
                        className="live-card"
                        key={stream.id}
                        data-testid="archived-stream-card"
                      >
                        <StreamPlaceholder stream={stream} />
                        <div className="live-card-body">
                          <span className="archive-status">
                            Captured snapshot — not current
                          </span>
                          <h3>{stream.title}</h3>
                          <p className="live-symbol">{stream.symbol}</p>
                          <dl>
                            <div>
                              <dt>Viewers at capture</dt>
                              <dd>
                                {stream.viewerCountAtCapture.toLocaleString(
                                  "en-US",
                                )}
                              </dd>
                            </div>
                            <div>
                              <dt>Creator</dt>
                              <dd title={stream.creatorAddress}>
                                {shortAddress(stream.creatorAddress)}
                              </dd>
                            </div>
                          </dl>
                          <button
                            type="button"
                            ref={(node) => {
                              if (node) cardRefs.current.set(stream.id, node);
                              else cardRefs.current.delete(stream.id);
                            }}
                            aria-label={`Inspect archived stream ${stream.title} ${stream.symbol}`}
                            aria-pressed={selected?.id === stream.id}
                            onClick={() => navigate({ stream: stream.id })}
                          >
                            Inspect archived metadata
                          </button>
                        </div>
                      </article>
                    ))}
                  </div>
                </>
              ) : (
                <div className="live-empty" data-testid="live-empty-results">
                  <h2>No matching captured record</h2>
                  <p>
                    Nothing in this {streams.length}-record archive matches the
                    local query. This says nothing about current broadcasts.
                  </p>
                </div>
              )}
            </>
          )}
        </section>

        <PlaybackPanel
          selected={selected}
          invalidSelection={invalidSelection}
          controlsReady={controlsReady}
          onClose={closeSelection}
        />
      </div>
    </div>
  );
}
