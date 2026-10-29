"use client";

import Link from "next/link";
import { Fragment, memo, type MouseEvent } from "react";
import {
  mentionProfileHref,
  planMentionText,
  type MentionSegment,
} from "../../../../../reconstruction/mention-text/model.mjs";
import styles from "./mention-text.module.css";

function stopPropagation(event: MouseEvent<HTMLElement>) {
  event.stopPropagation();
}

function InlineSegment({ segment }: { segment: MentionSegment }) {
  if (segment.kind === "mention") {
    return (
      <Link
        href={mentionProfileHref(segment.userId)!}
        prefetch={false}
        onClick={stopPropagation}
        className={styles.mention}
      >
        @{segment.username}
      </Link>
    );
  }
  if (segment.kind === "tweet") {
    return (
      <a
        href={segment.url}
        title={segment.url}
        target="_blank"
        rel="noopener noreferrer"
        data-testid="callout-tweet-chip"
        data-density="comfortable"
        className={styles.tweet}
        onClick={stopPropagation}
      >
        <span aria-hidden="true" className={styles.icon}>
          𝕏
        </span>
        <span className={styles.username}>@{segment.username}</span>
      </a>
    );
  }
  return segment.text;
}

/** Original standalone/default rendering path, for content outside an anchor. */
export const MentionText = memo(function MentionText({
  content,
}: {
  content: string;
}) {
  const plan = planMentionText(content);
  if (plan.plain !== null) return plan.plain;
  return plan.lines.map((line, index) => {
    const children = line.segments.map((segment, part) => (
      <InlineSegment key={part} segment={segment} />
    ));
    return (
      <Fragment key={index}>
        {line.greentext ? (
          <span data-testid="callout-greentext" className={styles.greentext}>
            {children}
          </span>
        ) : (
          children
        )}
        {line.lineBreakAfter ? "\n" : null}
      </Fragment>
    );
  });
});
