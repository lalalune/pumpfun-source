export const RECENT_SEARCHES_KEY = 'recently-searched-terms';

// The actual captured add/clear operations retain one render's term snapshot.
export function createRecentSearchAdder(terms, write) {
  return (term) => {
    let retained = terms.filter((entry) => entry !== term).slice(0, 19);
    write([term, ...retained]);
  };
}

export function createRecentSearchClearer(write) {
  return () => { write([]); };
}

// Only the original text-query destination is used; no identity enrichment.
export function recentSearchHref(row) {
  return `/explore?q=${encodeURIComponent(row.term)}`;
}

// Local boundary for browser-owned data. This is not the full original hook's
// deserializer, which did not establish a typed/corruption contract.
export function decodeRecentSearches(raw) {
  if (raw === null || raw === '') return [];
  const terms = JSON.parse(raw);
  if (!Array.isArray(terms) || terms.some((term) => typeof term !== 'string' || !term.isWellFormed())) {
    throw Error('Invalid stored search history');
  }
  return terms;
}
