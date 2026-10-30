/** Admit calendar-valid ISO observation instants without rewriting precision. */
export function isObservationInstant(value) {
  if (typeof value !== "string") return false;
  const parts = /^(\d{4}-\d{2}-\d{2})T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d+)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)$/.exec(value);
  if (!parts || !Number.isFinite(Date.parse(value))) return false;
  const calendar = new Date(`${parts[1]}T00:00:00Z`);
  return Number.isFinite(calendar.getTime()) &&
    calendar.toISOString().slice(0, 10) === parts[1];
}
