"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent,
  type ReactNode,
  type RefObject,
} from "react";
import { createPortal } from "react-dom";
import type { MenuEntry } from "@/config/navigation";
import { cn } from "@/lib/cn";

/*
 * A small accessible dropdown menu (menu button pattern). The captured triggers are
 * base-ui menu triggers, but their open popups were never server-rendered, so the
 * popup styling here is local design built from the captured tokens.
 */

export type MenuPlacement =
  | "bottom-start"
  | "bottom-end"
  | "top-start"
  | "top-end"
  | "right-start";

export interface MenuTriggerProps {
  ref: RefObject<HTMLButtonElement | null>;
  type: "button";
  "aria-haspopup": "menu";
  "aria-expanded": boolean;
  "aria-controls": string | undefined;
  "data-slot": "dropdown-menu-trigger";
  "data-popup-open"?: "";
  onClick: () => void;
  onKeyDown: (event: KeyboardEvent<HTMLButtonElement>) => void;
}

const GAP = 4;
const ITEM_SELECTOR = '[role="menuitem"]:not([aria-disabled="true"])';
const ITEM_CLASS =
  "flex h-8 w-full items-center whitespace-nowrap rounded-sm px-2 text-left text-text-secondary outline-none transition-colors hover:bg-bg-tertiary hover:text-text-primary focus-visible:bg-bg-tertiary focus-visible:text-text-primary";

function positionFor(rect: DOMRect, placement: MenuPlacement): CSSProperties {
  // Fixed positioning is relative to the viewport without the (stable) scrollbar gutter.
  const width = document.documentElement.clientWidth;
  const height = document.documentElement.clientHeight;
  switch (placement) {
    case "bottom-start":
      return { top: rect.bottom + GAP, left: rect.left };
    case "bottom-end":
      return { top: rect.bottom + GAP, right: width - rect.right };
    case "top-start":
      return { bottom: height - rect.top + GAP, left: rect.left };
    case "top-end":
      return { bottom: height - rect.top + GAP, right: width - rect.right };
    case "right-start":
      return { top: rect.top, left: rect.right + GAP };
  }
}

export function DropdownMenu({
  label,
  items,
  placement = "bottom-start",
  renderTrigger,
  onNavigate,
}: {
  label: string;
  items: readonly MenuEntry[];
  placement?: MenuPlacement;
  renderTrigger: (props: MenuTriggerProps) => ReactNode;
  onNavigate?: () => void;
}) {
  const id = useId();
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const [open, setOpen] = useState(false);
  const [position, setPosition] = useState<CSSProperties>({});

  const close = useCallback((restoreFocus: boolean) => {
    setOpen(false);
    if (restoreFocus) triggerRef.current?.focus();
  }, []);

  useLayoutEffect(() => {
    if (open && triggerRef.current)
      setPosition(
        positionFor(triggerRef.current.getBoundingClientRect(), placement),
      );
  }, [open, placement]);

  useEffect(() => {
    if (!open) return;
    menuRef.current?.querySelector<HTMLElement>(ITEM_SELECTOR)?.focus();
    const onPointerDown = (event: PointerEvent) => {
      const target = event.target as Node;
      if (
        !menuRef.current?.contains(target) &&
        !triggerRef.current?.contains(target)
      )
        close(false);
    };
    const onViewportChange = () => close(false);
    document.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("resize", onViewportChange);
    window.addEventListener("scroll", onViewportChange, true);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("resize", onViewportChange);
      window.removeEventListener("scroll", onViewportChange, true);
    };
  }, [open, close]);

  function onTriggerKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setOpen(true);
    }
  }

  function onMenuKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    const entries = Array.from(
      menuRef.current?.querySelectorAll<HTMLElement>(ITEM_SELECTOR) ?? [],
    );
    const index = entries.indexOf(document.activeElement as HTMLElement);
    const focusAt = (next: number) =>
      entries[(next + entries.length) % entries.length]?.focus();
    switch (event.key) {
      case "ArrowDown":
        event.preventDefault();
        focusAt(index + 1);
        break;
      case "ArrowUp":
        event.preventDefault();
        focusAt(index - 1);
        break;
      case "Home":
        event.preventDefault();
        focusAt(0);
        break;
      case "End":
        event.preventDefault();
        focusAt(entries.length - 1);
        break;
      case "Escape":
        event.preventDefault();
        close(true);
        break;
      case "Tab":
        // Restore the portal's origin before native Tab advances outside it.
        close(true);
        break;
    }
  }

  return (
    <>
      {renderTrigger({
        ref: triggerRef,
        type: "button",
        "aria-haspopup": "menu",
        "aria-expanded": open,
        "aria-controls": open ? id : undefined,
        "data-slot": "dropdown-menu-trigger",
        ...(open ? { "data-popup-open": "" as const } : {}),
        onClick: () => setOpen((current) => !current),
        onKeyDown: onTriggerKeyDown,
      })}
      {open &&
        createPortal(
          <div
            ref={menuRef}
            id={id}
            role="menu"
            aria-label={label}
            onKeyDown={onMenuKeyDown}
            style={{ position: "fixed", ...position }}
            className="z-[60] min-w-44 overflow-hidden rounded-md border border-border-tertiary bg-bg-secondary p-1 text-[13px] shadow-lg"
          >
            {items.map((item) => (
              <MenuItem
                key={item.label}
                item={item}
                onSelect={() => {
                  close(false);
                  onNavigate?.();
                }}
              />
            ))}
          </div>,
          document.body,
        )}
    </>
  );
}

function MenuItem({
  item,
  onSelect,
}: {
  item: MenuEntry;
  onSelect: () => void;
}) {
  if (!item.href) {
    return (
      <span
        role="menuitem"
        tabIndex={-1}
        aria-disabled="true"
        title={item.disabledReason}
        className={cn(
          ITEM_CLASS,
          "cursor-not-allowed opacity-50 hover:bg-transparent hover:text-text-secondary",
        )}
      >
        {item.label}
      </span>
    );
  }
  if (item.external) {
    return (
      <a
        role="menuitem"
        tabIndex={-1}
        href={item.href}
        target="_blank"
        rel="noopener noreferrer"
        className={ITEM_CLASS}
        onClick={onSelect}
      >
        {item.label}
      </a>
    );
  }
  return (
    <Link
      role="menuitem"
      tabIndex={-1}
      href={item.href}
      className={ITEM_CLASS}
      onClick={onSelect}
    >
      {item.label}
    </Link>
  );
}
