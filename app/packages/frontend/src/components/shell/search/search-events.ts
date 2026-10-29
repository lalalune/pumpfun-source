const OPEN_SEARCH_EVENT = 'pump:open-search';
const openListeners = new Set<() => void>();
let pendingOpen = false;

/** Ask the shell's search dialog to open. Triggers stay decoupled from the dialog. */
export function openSearch(): void {
  // A toolbar can hydrate before the dialog's separate Suspense boundary.
  if (openListeners.size === 0) pendingOpen = true;
  window.dispatchEvent(new Event(OPEN_SEARCH_EVENT));
}

export function onOpenSearch(listener: () => void): () => void {
  window.addEventListener(OPEN_SEARCH_EVENT, listener);
  openListeners.add(listener);
  if (pendingOpen) {
    pendingOpen = false;
    listener();
  }
  return () => {
    openListeners.delete(listener);
    window.removeEventListener(OPEN_SEARCH_EVENT, listener);
  };
}
