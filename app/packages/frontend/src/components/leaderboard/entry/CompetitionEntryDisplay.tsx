"use client";

import React, { type ComponentType } from "react";
import { jsx, jsxs } from "react/jsx-runtime";
import { useMemoCache } from "../original-prize-formats.mjs";
import {
  createEntryRow,
  type AvatarProps,
  type LinkProps,
} from "./original-entry-row";
import { createEntryHelpers } from "./entry-helpers.mjs";

/**
 * Create once outside render for an explicit source/host context.
 * Avatar and Link remain host-owned capabilities; no media, routing or API
 * implementation is silently substituted for the original providers.
 */
export function createCompetitionEntryComponents({
  squadVariant,
  imageVariant,
  useTranslation,
  Avatar,
  Link,
}: {
  squadVariant: string;
  imageVariant: string;
  useTranslation: () => {
    t: (key: string, values?: Record<string, string | number>) => string;
  };
  Avatar: ComponentType<AvatarProps>;
  Link: ComponentType<LinkProps>;
}) {
  const helpers = createEntryHelpers({ squadVariant, imageVariant, Intl });
  return createEntryRow({
    jsx,
    jsxs,
    React,
    useMemoCache,
    useTranslation,
    Avatar,
    Link,
    // Only the row's known nonconflicting size/color strings are used here.
    // The full captured class-merge implementation remains outside this unit.
    classNames: (...parts) => parts.filter(Boolean).join(" "),
    ...helpers,
  });
}
