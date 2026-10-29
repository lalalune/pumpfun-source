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
