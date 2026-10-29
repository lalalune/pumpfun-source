// Explicit original source context; never a guessed runtime winner.
export function createHelper({ emptyImage } = {}) {
  const t = { A: emptyImage };
  return (e) => {
    let i = e?.trim() ?? "";
    if (i && i !== t.A) return i;
  };
}
