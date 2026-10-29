// Explicit original source context; never a guessed runtime winner.
export function createHelper({ emptyImage } = {}) {
  const t = { A: emptyImage };
  return (e) => {
    let r = e?.trim() ?? "";
    if (r && r !== t.A) return r;
  };
}
