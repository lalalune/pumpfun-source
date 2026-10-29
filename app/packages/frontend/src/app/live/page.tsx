import type { Metadata } from "next";
import { Suspense } from "react";
import { loadLiveEvidence } from "./evidence";
import { loadLiveHeroEvidence } from "./hero-evidence";
import ArchivedLiveHero from "./archived-live-hero";
import LiveDiscovery from "./live-discovery";
import "./live.css";

export const metadata: Metadata = {
  title: "Live discovery",
  description:
    "Inspect a verified historical Live discovery snapshot without starting production playback.",
};

function DiscoveryFallback() {
  return (
    <section className="live-loading" role="status" aria-live="polite">
      <span aria-hidden="true" />
      Loading verified local discovery state…
    </section>
  );
}

export default async function LivePage() {
  const [evidence, hero] = await Promise.all([
    loadLiveEvidence(),
    loadLiveHeroEvidence(),
  ]);

  return (
    <section className="live-page" aria-labelledby="live-title">
      <header className="live-header">
        <div>
          <p className="eyebrow">Archived first-party evidence</p>
          <h1 id="live-title">Live discovery</h1>
          <p className="description">
            Browse all 42 cards in the captured Most viewers section. Captured
            order, sorting and page controls apply only to this archive. Records
            are historical, read-only and never refreshed from a production
            livestream service.
          </p>
        </div>
        <div className="live-safety-badge" aria-label="Live status boundary">
          <span aria-hidden="true" />
          No current live status
        </div>
      </header>

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
          {hero.ok ? (
            <ArchivedLiveHero streams={hero.snapshot.streams} />
          ) : (
            <aside
              role="alert"
              className="live-evidence-error"
              data-testid="archived-hero-error"
            >
              Archived highlights unavailable: the six-record hero data did not
              pass local evidence validation. No substitute or production data
              was loaded.
            </aside>
          )}
          <Suspense fallback={<DiscoveryFallback />}>
            <LiveDiscovery streams={evidence.snapshot.streams} />
          </Suspense>
          <footer className="live-provenance">
            Source: captured first-party <code>/live</code> HTML. SHA-256{" "}
            <code>{evidence.snapshot.sha256}</code>. External thumbnails,
            playlists, realtime presence, wallet actions and production playback
            are disabled.
          </footer>
        </>
      ) : (
        <section
          className="live-evidence-error"
          role="alert"
          data-testid="live-evidence-error"
        >
          <p className="playback-kicker">Fail-closed evidence adapter</p>
          <h2>Archived Live snapshot unavailable</h2>
          <p>
            The captured page did not pass local provenance, hash and schema
            checks. No synthetic cards or production fallback were used.
          </p>
        </section>
      )}
    </section>
  );
}
