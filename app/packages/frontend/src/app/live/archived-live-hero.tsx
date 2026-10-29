"use client";

import { useState } from "react";
import type { ArchivedStream } from "./live-data";
import "./live-hero.css";

export default function ArchivedLiveHero({
  streams,
}: {
  streams: ArchivedStream[];
}) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const selected = streams[selectedIndex];
  if (!selected) return null;

  return (
    <section
      className="archived-live-hero"
      aria-labelledby="archived-live-hero-heading"
    >
      <header>
        <p className="eyebrow">Captured highlights — no playback</p>
        <h2 id="archived-live-hero-heading">Archived highlights</h2>
        <p>
          The six original hero records, in captured order. These identities
          also occur in Most viewers; they are not six additional streams.
          Selection changes only the historical metadata below.
        </p>
      </header>
      <div
        className="archived-hero-choices"
        role="group"
        aria-label="Choose an archived highlight"
      >
        {streams.map((stream, index) => (
          <button
            key={stream.mint}
            type="button"
            data-testid="archived-hero-choice"
            data-selected={selectedIndex === index}
            aria-current={selectedIndex === index ? "true" : undefined}
            aria-controls="archived-hero-metadata"
            aria-label={`Show archived highlight ${index + 1} of ${streams.length}: ${stream.symbol}`}
            onClick={() => setSelectedIndex(index)}
          >
            <span>{index + 1}</span>
            <strong>{stream.symbol}</strong>
          </button>
        ))}
      </div>
      <article
        id="archived-hero-metadata"
        className="archived-hero-metadata"
        aria-labelledby="archived-hero-title"
        data-testid="archived-hero-metadata"
      >
        <div aria-live="polite" aria-atomic="true">
          <p>
            Archived highlight {selectedIndex + 1} of {streams.length}
          </p>
          <h3 id="archived-hero-title">{selected.title}</h3>
          <p className="archived-hero-symbol">{selected.symbol}</p>
        </div>
        <dl>
          <div>
            <dt>Viewers at capture</dt>
            <dd>{selected.viewerCountAtCapture.toLocaleString("en-US")}</dd>
          </div>
          <div>
            <dt>Creator address</dt>
            <dd>{selected.creatorAddress}</dd>
          </div>
          <div>
            <dt>Mint</dt>
            <dd>{selected.mint}</dd>
          </div>
        </dl>
        <p>
          Marked live at capture. Current presence, thumbnails and playback are
          unavailable.
        </p>
      </article>
      <div
        className="archived-hero-controls"
        role="group"
        aria-label="Archived highlight navigation"
      >
        <button
          type="button"
          onClick={() =>
            setSelectedIndex(
              (index) => (index - 1 + streams.length) % streams.length,
            )
          }
        >
          Previous archived highlight
        </button>
        <button
          type="button"
          onClick={() =>
            setSelectedIndex((index) => (index + 1) % streams.length)
          }
        >
          Next archived highlight
        </button>
      </div>
    </section>
  );
}
