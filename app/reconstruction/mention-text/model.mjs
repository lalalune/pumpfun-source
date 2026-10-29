// Independent reconstruction of 314012.m and the default standalone 174251.f
// content path. Captured factories are evidence and are never executed.
export function parseMentions(content) {
  if (!content.includes("@["))
    return content ? [{ kind: "text", text: content }] : [];
  const pattern = /@\[([A-Za-z0-9_]{1,15})\]\(([0-9a-fA-F-]{36})\)/g;
  const segments = [];
  let cursor = 0;
  for (
    let match = pattern.exec(content);
    match;
    match = pattern.exec(content)
  ) {
    if (match.index > cursor)
      segments.push({ kind: "text", text: content.slice(cursor, match.index) });
    segments.push({ kind: "mention", username: match[1], userId: match[2] });
    cursor = match.index + match[0].length;
  }
  if (cursor < content.length)
    segments.push({ kind: "text", text: content.slice(cursor) });
  return segments;
}

export function mentionProfileHref(userId) {
  return userId ? `/profile/${encodeURIComponent(userId)}` : null;
}

function tweetStatus(url) {
  let parsed;
  try {
    parsed = new URL(url);
  } catch {
    return null;
  }
  if (!/^(?:[\w-]+\.)?(?:twitter|x)\.com$/i.test(parsed.hostname)) return null;
  const match = parsed.pathname.match(/^\/([^/]+)\/status\/(\d+)/);
  return match?.[2] ? { id: match[2], username: match[1], url } : null;
}

function textWithTweetStatuses(text) {
  if (!text.includes("/status/")) return text ? [{ kind: "text", text }] : [];
  const pattern = /(https?:\/\/(?:[^\s"'(),;<>\]`]+|\([^\s"'(),;<>\]`]*\))+)/gi;
  const segments = [];
  let cursor = 0;
  for (let match = pattern.exec(text); match; match = pattern.exec(text)) {
    const url = match[0].replace(/[!,.:;?]+$/, "");
    const status = tweetStatus(url);
    if (!status) continue;
    if (match.index > cursor)
      segments.push({ kind: "text", text: text.slice(cursor, match.index) });
    segments.push({ kind: "tweet", ...status });
    cursor = match.index + url.length;
  }
  if (cursor < text.length)
    segments.push({ kind: "text", text: text.slice(cursor) });
  return segments;
}

function inlineMentionText(content) {
  return parseMentions(content).flatMap((segment) =>
    segment.kind === "text" ? textWithTweetStatuses(segment.text) : [segment],
  );
}

export function planMentionText(content) {
  const greentext = /(?:^|\n)[ \t]*>/.test(content);
  if (!greentext && !content.includes("@[") && !content.includes("/status/"))
    return { plain: content, lines: [] };
  const lines = greentext ? content.split("\n") : [content];
  return {
    plain: null,
    lines: lines.map((text, index) => ({
      greentext: greentext && /^[ \t]*>/.test(text),
      segments: inlineMentionText(text),
      lineBreakAfter: index < lines.length - 1,
    })),
  };
}
