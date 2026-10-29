"use client";

import React, { type ComponentType } from "react";
import { jsx, jsxs } from "react/jsx-runtime";
import { useMemoCache } from "../original-prize-formats.mjs";
import { createEntryHelpers } from "../entry/entry-helpers.mjs";
import type { AvatarProps } from "../entry/original-entry-row";
import { createViewerCard, type ViewerLinkProps } from "./original-viewer-card";
import { createVolumeFormatter } from "./original-volume.mjs";

/** Create once outside render in a client module. No account/price is inferred. */
export function createCompetitionViewerComponents({
  squadVariant,
  imageVariant,
  useTranslation,
  useSolPrice,
  Avatar,
  Link,
}: {
  squadVariant: string;
  imageVariant: string;
  useTranslation: () => {
    t: (key: string, values?: Record<string, string | number>) => string;
  };
  useSolPrice: (options: Record<string, never>) => { data?: number | null };
  Avatar: ComponentType<AvatarProps>;
  Link: ComponentType<ViewerLinkProps>;
}) {
  const helpers = createEntryHelpers({ squadVariant, imageVariant, Intl });
  return createViewerCard({
    jsx,
    jsxs,
    React,
    useMemoCache,
    useTranslation,
    useSolPrice,
    Avatar,
    Link,
    classNames: (...parts) => parts.filter(Boolean).join(" "),
    formatVolume: createVolumeFormatter(Intl),
    ...helpers,
  });
}
