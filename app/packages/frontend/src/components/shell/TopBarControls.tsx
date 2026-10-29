'use client';

import { usePathname, useRouter } from 'next/navigation';
import { CREATE_MENU } from '@/config/navigation';
import { DropdownMenu } from '@/components/ui/dropdown-menu';
import { BackIcon, SearchIcon, SearchMobileIcon, TopbarCreateIcon } from './captured-icons';
import { openSearch } from './search/search-events';
import { ICON_BUTTON_CLASS } from './styles';

/* The interactive parts of the top bar; the rest of it renders on the server. */

const BACK_HIDDEN_PATHS = new Set(['/', '/go', '/live']);

export function BackButton() {
  const pathname = usePathname();
  const router = useRouter();
  if (BACK_HIDDEN_PATHS.has(pathname)) return null;

  function goBack() {
    if (window.history.length > 1) router.back();
    else router.push('/');
  }

  return (
    <button type="button" aria-label="Go back" className={ICON_BUTTON_CLASS} onClick={goBack}>
      <BackIcon />
    </button>
  );
}

export function SearchBox() {
  return (
    <div
      className="group w-full max-w-[420px] relative flex min-w-0 items-center rounded-md border border-border-tertiary bg-bg-tertiary transition-colors h-8 focus-within:border-border-tertiary has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-text-accent"
      role="search"
    >
      <SearchIcon />
      <button
        type="button"
        onClick={openSearch}
        className="flex h-full w-full min-w-0 items-center text-left focus-visible:outline-none pl-8 text-[13px] leading-[18px] pr-2.5"
        aria-label="Search for coins and users"
        aria-keyshortcuts="Meta+K Control+K"
      >
        <span className="min-w-0 flex-1 truncate text-text-quaternary transition-colors group-hover:text-text-tertiary">Search for coins and users...</span>
        <kbd
          data-slot="kbd"
          className="shrink-0 items-center gap-1 whitespace-nowrap rounded-sm px-1.5 font-medium tabular-nums [&>svg]:size-3 [&>svg]:shrink-0 h-5 text-xs leading-4 pointer-events-none ml-2 hidden select-none bg-bg-quaternary font-sans text-text-quaternary sm:inline-flex"
        >
          ⌘K
        </kbd>
      </button>
    </div>
  );
}

export function SearchIconButton() {
  return (
    <button aria-label="Search for coins and users" className={ICON_BUTTON_CLASS} type="button" onClick={openSearch}>
      <SearchMobileIcon />
    </button>
  );
}

export function CreateMenuButton() {
  return (
    <DropdownMenu
      label="Create"
      items={CREATE_MENU}
      placement="bottom-end"
      renderTrigger={(props) => (
        <button
          {...props}
          aria-label="Create"
          data-density="comfortable"
          data-size="32"
          data-variant="outlined"
          data-testid="topbar-create-button"
          className="inline-flex shrink-0 items-center justify-center rounded-md transition-colors focus-visible:ring-text-accent disabled:cursor-not-allowed disabled:opacity-40 [&>svg]:shrink-0 size-8 [&>svg]:size-4 border border-border-tertiary bg-transparent text-text-tertiary hover:bg-bg-tertiary hover:text-text-primary focus-visible:ring-0 focus-visible:outline focus-visible:outline-2 focus-visible:outline-text-accent data-[popup-open]:bg-bg-tertiary data-[popup-open]:text-text-primary"
        >
          <TopbarCreateIcon />
        </button>
      )}
    />
  );
}
