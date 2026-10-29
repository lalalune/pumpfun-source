import Link from "next/link";
import { RelativeTime } from "./RelativeTime";
import type { NativeCallout, NativeFeedKind } from "./native-feed-data";
import {
  NATIVE_FEED_MAX_TRAIL,
  nativeFeedHref,
} from "./native-feed-navigation";
import type { NativeFeedLoadResult } from "./native-feed-server";

const money = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 2,
});

function assetClassLabel(value: string): string {
  if (value === "ASSET_CLASS_PERPETUAL") return "Perpetual";
  if (value === "ASSET_CLASS_NFT_LIKE") return "Collectible";
  return "Token";
}

function NativeCalloutCard({ callout }: { callout: NativeCallout }) {
  const headingId = `native-callout-${callout.id}`;
  return (
    <article
      className="native-callout-card"
      data-testid="native-callout-card"
      aria-labelledby={headingId}
    >
      <header className="native-callout-header">
        <div className="native-callout-title">
          <span className="native-callout-image-state">
            No local image supplied
          </span>
          <p className="native-callout-symbol">
            {callout.symbol} · {callout.chain} ·{" "}
            {assetClassLabel(callout.assetClass)}
          </p>
          <h2 id={headingId}>{callout.coinName}</h2>
        </div>
        <span className="feed-source-chip">Synthetic local callout</span>
      </header>

      <p className="native-callout-thesis">{callout.thesis}</p>

      <dl className="native-callout-metrics" aria-label="Local snapshot fields">
        <div>
          <dt>Local market cap</dt>
          <dd>{money.format(callout.marketCapUsd)}</dd>
        </div>
        <div>
          <dt>At callout</dt>
          <dd>{money.format(callout.calledOutAtMarketCapUsd)}</dd>
        </div>
        <div>
          <dt>Local multiple</dt>
          <dd>{callout.multiple.toFixed(2)}×</dd>
        </div>
        <div>
          <dt>Local cost basis</dt>
          <dd>{money.format(callout.costBasisUsd)}</dd>
        </div>
      </dl>

      <footer className="native-callout-footer">
        <div>
          <strong>{callout.authorName}</strong>
          <span>{callout.authorId}</span>
        </div>
        <RelativeTime timestamp={callout.calloutTimestamp} showTitle />
      </footer>
      <p className="native-callout-mint">
        <span>Local coin identifier</span>
        <code>{callout.coinMint}</code>
      </p>
    </article>
  );
}

function NativeFeedState({
  result,
}: {
  result: Extract<NativeFeedLoadResult, { ok: false }>;
}) {
  const invalidCursor = result.reason === "invalid-cursor";
  return (
    <section
      className="feed-state-card"
      data-testid="native-feed-error"
      role="status"
    >
      <span className="feed-state-mark" aria-hidden="true">
        !
      </span>
      <h2>
        {invalidCursor
          ? "Local page cursor rejected"
          : "Local callouts unavailable"}
      </h2>
      <p>
        {invalidCursor
          ? "The local backend did not accept this opaque page token. Return to the first local page to continue."
          : "The opt-in local backend could not provide a validated response. No live or synthetic fallback was generated."}
      </p>
      <Link className="feed-state-link" href={nativeFeedHref("ranked")}>
        Return to first local page
      </Link>
    </section>
  );
}

type NativeCalloutFeedProps = {
  kind: NativeFeedKind;
  cursor?: string;
  trail: readonly string[];
  result: NativeFeedLoadResult;
};

export function NativeCalloutFeed({
  kind,
  cursor,
  trail,
  result,
}: NativeCalloutFeedProps) {
  const historyLimitReached = Boolean(
    cursor && trail.length >= NATIVE_FEED_MAX_TRAIL,
  );
  return (
    <div className="native-callout-view">
      <aside
        className="feed-provenance native-feed-provenance"
        aria-label="Local callout source"
      >
        <strong>Synthetic local callout data</strong>
        <span>
          Not live Pump.fun activity. Values come from the opt-in local
          reconstruction backend and carry local-unqualified compatibility.
        </span>
      </aside>

      <nav
        className="native-feed-view-tabs"
        aria-label="Local callout ordering"
      >
        <Link
          href={nativeFeedHref("ranked")}
          aria-current={kind === "ranked" ? "page" : undefined}
        >
          Local ranked
        </Link>
        <Link
          href={nativeFeedHref("newest")}
          aria-current={kind === "newest" ? "page" : undefined}
        >
          Local newest
        </Link>
      </nav>

      {!result.ok ? (
        <NativeFeedState result={result} />
      ) : result.page.coins.length === 0 ? (
        <section className="feed-state-card" data-testid="native-feed-empty">
          <span className="feed-state-mark" aria-hidden="true">
            C
          </span>
          <h2>No local callouts on this page</h2>
          <p>
            The bounded local dataset returned an empty result. This says
            nothing about current Pump.fun activity.
          </p>
        </section>
      ) : (
        <>
          {kind === "newest" && result.count ? (
            <p className="native-feed-count" data-testid="native-feed-count">
              {result.count.newCount}
              {result.count.capped ? "+" : ""} newer local callouts relative to
              this local snapshot.
            </p>
          ) : null}
          <div
            className="native-callout-list"
            aria-label="Synthetic local callouts"
          >
            {result.page.coins.map((callout) => (
              <NativeCalloutCard key={callout.id} callout={callout} />
            ))}
          </div>

          <nav
            className="native-feed-pagination"
            aria-label="Local callout pages"
          >
            {cursor ? (
              <Link
                rel="prev"
                href={nativeFeedHref(kind, trail.at(-1), trail.slice(0, -1))}
              >
                ← Previous
              </Link>
            ) : (
              <span aria-disabled="true">← Previous</span>
            )}
            <strong>Local page {trail.length + (cursor ? 2 : 1)}</strong>
            {result.page.nextPageToken && historyLimitReached ? (
              <span aria-disabled="true">Local navigation limit</span>
            ) : result.page.nextPageToken ? (
              <Link
                rel="next"
                href={nativeFeedHref(
                  kind,
                  result.page.nextPageToken,
                  cursor ? [...trail, cursor] : trail,
                )}
              >
                Next →
              </Link>
            ) : (
              <span aria-disabled="true">End of local list</span>
            )}
          </nav>
          {result.page.nextPageToken && historyLimitReached ? (
            <p className="native-feed-count" role="status">
              More local records are available, but this preview limits
              pagination history to {NATIVE_FEED_MAX_TRAIL} saved cursors. Go
              back or{" "}
              <Link className="feed-state-link" href={nativeFeedHref(kind)}>
                return to the first local page
              </Link>
              .
            </p>
          ) : null}
        </>
      )}
    </div>
  );
}
