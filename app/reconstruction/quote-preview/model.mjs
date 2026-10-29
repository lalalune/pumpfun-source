// Independent reconstruction of the standalone comfortable 386028.f path.
export const DELETED_TRANSLATION_KEY = "profile.reposts.deleted_post";
export function quotePreviewPlan(quoted) {
  const author =
    quoted.authorName ??
    (quoted.authorAddress
      ? quoted.authorAddress.length <= 9
        ? quoted.authorAddress
        : `${quoted.authorAddress.slice(0, 4)}…${quoted.authorAddress.slice(-4)}`
      : undefined);
  if (quoted.deleted)
    return { kind: "unavailable", translationKey: DELETED_TRANSLATION_KEY };
  return { kind: "quote", author: author || null, text: quoted.text || null };
}
