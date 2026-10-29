import type { ReactNode } from "react";
import {
  quotePreviewPlan,
  type QuotePreviewData,
} from "../../../../../reconstruction/quote-preview/model.mjs";
import { MentionText } from "./MentionText";
import styles from "./quote-preview.module.css";

/** Original386028.f standalone comfortable path; unavailable copy is injected. */
export function QuotePreview({
  quoted,
  unavailableLabel,
}: {
  quoted: QuotePreviewData;
  unavailableLabel: ReactNode;
}) {
  const plan = quotePreviewPlan(quoted);
  return (
    <blockquote data-testid="feed-quote-embed" className={styles.preview}>
      {plan.kind === "unavailable" ? (
        <p className={styles.unavailable}>{unavailableLabel}</p>
      ) : (
        <>
          {plan.author ? <p className={styles.author}>{plan.author}</p> : null}
          {plan.text ? (
            <p className={styles.text}>
              <MentionText content={plan.text} />
            </p>
          ) : null}
        </>
      )}
    </blockquote>
  );
}
