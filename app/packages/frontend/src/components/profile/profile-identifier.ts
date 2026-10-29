export function isValidProfileIdentifier(value: string): boolean {
  return (
    value.length > 0 &&
    value.length <= 128 &&
    value === value.trim() &&
    !/[/?#\\\u0000-\u001f\u007f]/u.test(value)
  );
}
