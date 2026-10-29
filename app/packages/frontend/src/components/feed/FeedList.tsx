import { FeedItem } from "./FeedItem";
import { LocalQuoteRow } from "./LocalQuoteRow";
import type { LocalFeedPost } from "./feed-data";

type FeedListProps = {
  items: readonly LocalFeedPost[];
};

/** A semantic, read-only list of validated local example posts. */
export function FeedList({ items }: FeedListProps) {
  if (items.length === 0) {
    return (
      <section className="feed-state-card" data-testid="local-feed-empty">
        <span className="feed-state-mark" aria-hidden="true">
          P
        </span>
        <h2>No local example posts</h2>
        <p>
          The checked-in dataset contains no valid visible root posts. This says
          nothing about activity on the live Pump service.
        </p>
      </section>
    );
  }

  return (
    <div className="feed-list" role="feed" aria-label="Local example posts">
      {items.map((item) =>
        item.quotePreview ? (
          <LocalQuoteRow
            key={item.id}
            item={{ ...item, quotePreview: item.quotePreview }}
          />
        ) : (
          <FeedItem key={item.id} item={item} />
        ),
      )}
    </div>
  );
}
