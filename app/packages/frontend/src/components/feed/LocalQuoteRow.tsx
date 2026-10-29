import type { LocalFeedPost } from "./feed-data";
import { FeedItem } from "./FeedItem";
import { QuotePreview } from "./QuotePreview";
import styles from "./quote-preview.module.css";

/** New local at-rest host adaptation; not a recovered original coordinator. */
export function LocalQuoteRow({
  item,
}: {
  item: LocalFeedPost & {
    quotePreview: NonNullable<LocalFeedPost["quotePreview"]>;
  };
}) {
  return (
    <div
      className={styles.row}
      data-local-post-kind="quote"
      role="group"
      aria-label="Recorded local quote"
    >
      <FeedItem item={item} />
      <div className={styles.inlay}>
        <span className={styles.localLabel}>Quoted local record</span>
        <QuotePreview
          quoted={item.quotePreview}
          unavailableLabel="Quoted local record unavailable"
        />
      </div>
    </div>
  );
}
