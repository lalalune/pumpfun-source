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
