export type MentionSegment =
  | { kind: "text"; text: string }
  | { kind: "mention"; username: string; userId: string }
  | { kind: "tweet"; username: string; id: string; url: string };
export function parseMentions(content: string): MentionSegment[];
export function mentionProfileHref(userId: string): string | null;
export function planMentionText(content: string): {
  plain: string | null;
  lines: {
    greentext: boolean;
    segments: MentionSegment[];
    lineBreakAfter: boolean;
  }[];
};
