// Explicit original source context; never a guessed runtime winner.
export function createHelper({ emptyImage } = {}) {
  const r = { A: emptyImage };
  return (e) => {
    let s = e?.trim() ?? "";
    if (s && s !== r.A) return s;
  };
}
