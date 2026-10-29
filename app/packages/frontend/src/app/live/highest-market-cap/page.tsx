import type { Metadata } from "next";
import Link from "next/link";
import { loadLiveEvidence } from "../evidence";
import "../live.css";

export const metadata: Metadata = {
  title: "Archived Highest market cap streams",
  description: "Read the separately captured Highest market cap Live section.",
};

export default async function HighestMarketCapPage() {
  const evidence = await loadLiveEvidence("highest-market-cap");

  return (
    <section className="live-page" aria-labelledby="live-highest-title">
      <header className="live-header">
        <div>
          <p className="eyebrow">Archived first-party evidence</p>
          <h1 id="live-highest-title">Highest market cap</h1>
          <p className="description">
            The 24 cards from the second section of the captured Live page, in
            its recorded order. The section name comes from the original
            renderer; this archive does not calculate market caps, rank current
            coins or establish a broadcast’s current status.
          </p>
        </div>
        <div className="live-safety-badge" aria-label="Live status boundary">
          <span aria-hidden="true" />
          No current live status
        </div>
      </header>

      <nav aria-label="Archived Live navigation">
        <Link className="live-archive-link" href="/live">
          Return to captured Most viewers
        </Link>
      </nav>

      {evidence.ok ? (
        <>
          <aside
            className="live-snapshot-note"
            aria-label="Snapshot provenance"
          >
            <strong>Authenticated local snapshot</strong>
            <span>
              Captured{" "}
              <time dateTime={evidence.snapshot.capturedAt}>
                {evidence.snapshot.capturedAt}
              </time>
            </span>
            <span>{evidence.snapshot.streams.length} exact archived cards</span>
          </aside>
          <p className="live-provenance">
            These 24 records also occur in Most viewers, with different section
            membership and order. They are not 24 additional streams. Open a
            card’s metadata locally; no media session starts.
          </p>
          <section
            className="stream-grid"
            aria-label="Archived Highest market cap cards"
          >
            {evidence.snapshot.streams.map((stream) => (
              <article
                className="live-card"
                key={stream.id}
                data-testid="highest-archived-card"
              >
                <span className="live-card-art" aria-hidden="true">
                  <span>{stream.symbol.slice(0, 3)}</span>
                  <small>Archived preview withheld</small>
                </span>
                <div className="live-card-body">
                  <span className="archive-status">
                    Captured snapshot — not current
                  </span>
                  <h2>{stream.title}</h2>
                  <p className="live-symbol">{stream.symbol}</p>
                  <details className="live-archived-details">
                    <summary>
                      Inspect archived metadata for {stream.symbol}
                    </summary>
                    <dl>
                      <div>
                        <dt>Viewers at capture</dt>
                        <dd>
                          {stream.viewerCountAtCapture.toLocaleString("en-US")}
                        </dd>
                      </div>
                      <div>
                        <dt>Creator address</dt>
                        <dd>{stream.creatorAddress}</dd>
                      </div>
                      <div>
                        <dt>Mint</dt>
                        <dd>{stream.mint}</dd>
                      </div>
                    </dl>
                    <p>
                      Marked live at capture. Playback and current presence are
                      unavailable.
                    </p>
                  </details>
                </div>
              </article>
            ))}
          </section>
          <footer className="live-provenance">
            Source: second section of captured first-party <code>/live</code>{" "}
            HTML. SHA-256 <code>{evidence.snapshot.sha256}</code>. External
            thumbnails, playlists, wallet actions and production playback are
            disabled.
          </footer>
        </>
      ) : (
        <section
          className="live-evidence-error"
          role="alert"
          data-testid="highest-evidence-error"
        >
          <p className="playback-kicker">Fail-closed evidence adapter</p>
          <h2>Archived Highest market cap snapshot unavailable</h2>
          <p>
            The capture did not pass local provenance, hash and schema checks.
            No replacement cards or production fallback were used.
          </p>
        </section>
      )}
    </section>
  );
}
