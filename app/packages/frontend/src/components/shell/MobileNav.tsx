"use client";

import Link from "next/link";
import { CREATE_MENU } from "@/config/navigation";
import { useSidebar } from "@/components/ui/sidebar";
import { DropdownMenu } from "@/components/ui/dropdown-menu";
import {
  MobileCreateIcon,
  MobileExploreIcon,
  MobileGoIcon,
  MobileHomeIcon,
  MobileMenuIcon,
} from "./captured-icons";

const ITEM_CLASS = "flex flex-col items-center justify-center p-2 text-white";
// The captured triggers set outline-none; keep a visible keyboard focus ring.
const FOCUS_RING =
  "focus-visible:outline focus-visible:outline-2 focus-visible:outline-text-accent";

/**
 * Fixed bottom navigation below the `md` breakpoint. Its captured DOM position
 * precedes the header. More opens the maintained accessible mobile drawer;
 * the captured closed-state icon/placement is preserved, not an upstream popup claim.
 */
export function MobileNav() {
  const { openMobile, mobileOpen, mobileTrigger, isMobile } = useSidebar();
  return (
    <div className="md:hidden" inert={mobileOpen}>
      <nav
        aria-label="Mobile"
        className="left-0 right-0 z-50 mt-16 flex items-center justify-around border-t border-t-[rgba(248,250,252,0.1)] bg-bg-secondary pt-2"
        style={{
          position: "fixed",
          bottom: 0,
          paddingBottom: "calc(8px + env(safe-area-inset-bottom))",
        }}
      >
        <div
          aria-hidden="true"
          data-testid="mobile-nav-glass-bleed"
          className="pointer-events-none absolute inset-x-0 top-full bg-bg-secondary"
          style={{ height: 128 }}
        />
        <Link
          href="/"
          aria-label="Home"
          className={`${ITEM_CLASS} ${FOCUS_RING}`}
        >
          <MobileHomeIcon />
        </Link>
        <Link
          href="/explore"
          aria-label="Explore"
          className={`${ITEM_CLASS} ${FOCUS_RING}`}
        >
          <MobileExploreIcon />
        </Link>
        <DropdownMenu
          label="Create"
          items={CREATE_MENU}
          placement="top-start"
          renderTrigger={(props) => (
            <button
              {...props}
              aria-label="Create"
              data-testid="create-button-mobile-nav"
              className={`flex flex-col items-center justify-center p-2 outline-none text-white ${FOCUS_RING}`}
            >
              <MobileCreateIcon />
            </button>
          )}
        />
        <Link
          href="/go"
          aria-label="GO"
          className={`${ITEM_CLASS} ${FOCUS_RING}`}
        >
          <MobileGoIcon />
        </Link>
        <button
          type="button"
          ref={mobileTrigger}
          onClick={openMobile}
          disabled={!isMobile}
          aria-busy={!isMobile}
          aria-label="Open navigation"
          title={isMobile ? "More" : "Loading navigation…"}
          aria-controls="app-sidebar"
          aria-expanded={mobileOpen}
          className={`flex min-h-11 min-w-11 flex-col items-center justify-center p-2 text-white outline-none disabled:cursor-wait disabled:opacity-50 ${FOCUS_RING}`}
        >
          <MobileMenuIcon />
        </button>
      </nav>
    </div>
  );
}
