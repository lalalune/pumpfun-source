import Link from "next/link";
import { isValidProfileIdentifier } from "../profile/profile-identifier";
import type { LocalFeedPost } from "./feed-data";

function initial(name: string): string {
  return Array.from(name.trim())[0]?.toLocaleUpperCase("en-US") ?? "?";
}
function shortAddress(address: string): string {
  if (address.length <= 14) return address;
  return `${address.slice(0, 6)}…${address.slice(-4)}`;
}

/** A read-only local example post. No control initiates a social mutation. */
export function FeedItem({ item }: { item: LocalFeedPost }) {
  const headingId = `feed-author-${item.id}`;
  const contentId = `feed-content-${item.id}`;
  const profileIdentifier = item.author.missing
    ? undefined
    : [item.author.address, item.author.userId].find(
        (value): value is string =>
          typeof value === "string" && isValidProfileIdentifier(value),
      );

  return (
    <article
      className="feed-item"
      data-testid="local-feed-item"
      data-source={item.dataSource}
      aria-labelledby={headingId}
      aria-describedby={contentId}
    >
      <div className="feed-avatar" aria-hidden="true">
        {initial(item.author.name)}
      </div>
      <div className="feed-item-body">
        <header className="feed-item-header">
          <div className="feed-author-block">
            <h2 id={headingId}>
              {profileIdentifier ? (
                <Link
                  href={`/profile/${encodeURIComponent(profileIdentifier)}`}
                  prefetch={false}
                  className="hover:underline"
                >
                  {item.author.name}
                </Link>
              ) : (
                item.author.name
              )}
            </h2>
            <span className="feed-author-address">
              {item.author.missing
                ? "Unresolved seed identity"
                : item.author.address
                  ? shortAddress(item.author.address)
                  : "No wallet address recorded."}
            </span>
          </div>
          <time dateTime={item.timestamp}>{item.timestampLabel}</time>
        </header>

        <span className="feed-source-chip">Synthetic example</span>
        <p id={contentId} className="feed-content">
          {item.content ?? "No text content was included in this local record."}
        </p>

        {item.hasMedia ? (
          <div
            className="feed-media-placeholder"
            role="img"
            aria-label="External media withheld in offline mode"
          >
            <span aria-hidden="true">▧</span>
            <strong>Media unavailable offline</strong>
            <small>The recorded external URL was not requested.</small>
          </div>
        ) : null}

        <dl
          className="feed-engagement"
          aria-label="Read-only engagement counts"
        >
          <div>
            <dt>Likes</dt>
            <dd>{item.likes}</dd>
          </div>
          <div>
            <dt>Reposts</dt>
            <dd>{item.reposts}</dd>
          </div>
          <div>
            <dt>Replies</dt>
            <dd>{item.replies}</dd>
          </div>
          <div>
            <dt>Quotes</dt>
            <dd>{item.quotes}</dd>
          </div>
        </dl>
      </div>
    </article>
  );
}
