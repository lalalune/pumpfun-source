export type QuotePreviewData = {
  deleted?: boolean;
  authorName?: string | null;
  authorAddress?: string | null;
  text?: string | null;
};
export const DELETED_TRANSLATION_KEY: "profile.reposts.deleted_post";
export function quotePreviewPlan(
  quoted: QuotePreviewData,
):
  | { kind: "unavailable"; translationKey: typeof DELETED_TRANSLATION_KEY }
  | { kind: "quote"; author: string | null; text: string | null };
