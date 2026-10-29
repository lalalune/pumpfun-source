export function isValidProfileIdentifier(value: string): boolean {
  return (
    value.length > 0 &&
    value.length <= 128 &&
    value === value.trim() &&
    value !== "." &&
    value !== ".." &&
    // With the Unicode flag, valid surrogate pairs are code points outside this range.
    // Lone surrogates cannot be passed to encodeURIComponent without throwing.
    !/[\ud800-\udfff]/u.test(value) &&
    !/[/?#\\\u0000-\u001f\u007f]/u.test(value)
  );
}
