import type { Metadata } from "next";
import { Suspense } from "react";
import LeaderboardClient from "./leaderboard-client";

export const metadata: Metadata = {
  title: "Leaderboard",
  description:
    "Evidence-backed trader rankings, creator payouts and competitions interface.",
};

function LeaderboardFallback() {
  return (
    <section
      className="leaderboard-loading"
      aria-busy="true"
      aria-live="polite"
    >
      <span className="leaderboard-spinner" aria-hidden="true" />
      <p>Preparing leaderboard controls…</p>
    </section>
  );
}

export default function LeaderboardPage() {
  return (
    <>
      <div className="leaderboard-heading">
        <div>
          <p className="eyebrow">Verified read-only contract</p>
          <h1>Leaderboard</h1>
          <p className="description">
            Trader PnL, creator payouts and competitions from documented
            developer reads. Rankings only appear after a response passes
            runtime validation.
          </p>
        </div>
        <span className="read-only-badge">Read only</span>
      </div>
      <Suspense fallback={<LeaderboardFallback />}>
        <LeaderboardClient />
      </Suspense>
    </>
  );
}
