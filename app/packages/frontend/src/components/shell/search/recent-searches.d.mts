export const RECENT_SEARCHES_KEY: 'recently-searched-terms';
export function createRecentSearchAdder(terms: readonly string[], write: (terms: string[]) => void): (term: string) => void;
export function createRecentSearchClearer(write: (terms: string[]) => void): () => void;
export function recentSearchHref(row: { term: string }): string;
export function decodeRecentSearches(raw: string | null): string[];
