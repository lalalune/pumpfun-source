"use client";

import React, { type ComponentType, type FunctionComponent } from "react";
import { jsx, jsxs } from "react/jsx-runtime";
import {
  useMemoCache,
  createPrizeFormats,
} from "../original-prize-formats.mjs";
import { createCompetitionPrizeComponents } from "../CompetitionPrizeDisplay";
import { createCompetitionEntryComponents } from "../entry/CompetitionEntryDisplay";
import { createCompetitionViewerComponents } from "../viewer/CompetitionViewerDisplay";
import type { AvatarProps } from "../entry/original-entry-row";
import type { ViewerLinkProps } from "../viewer/original-viewer-card";
import {
  createCompetitionBoard,
  type BoardClient,
  type HeroProps,
  type HighlightProps,
  type RulesProps,
  type CardProps,
} from "./original-board";

/** Stable source-context composition. Every unresolved provider remains explicit. */
export function createCompetitionBoardComponents({
  squadVariant,
  imageVariant,
  numberVariant,
  useTranslation,
  useSolPrice,
  useReducedMotion,
  Avatar,
  Link,
  client,
  Hero,
  Highlights,
  Rules,
  Card,
}: {
  squadVariant: string;
  imageVariant: string;
  numberVariant: string;
  useTranslation: () => {
    t: (key: string, values?: Record<string, string | number>) => string;
    i18n: { language: string };
  };
  useSolPrice: (options: Record<string, never>) => { data?: number | null };
  useReducedMotion: () => boolean | null | undefined;
  Avatar: ComponentType<AvatarProps>;
  Link: FunctionComponent<
    Omit<ViewerLinkProps, "aria-label"> & { "aria-label"?: string }
  >;
  client: BoardClient;
  Hero: ComponentType<HeroProps>;
  Highlights: ComponentType<HighlightProps>;
  Rules: ComponentType<RulesProps>;
  Card: ComponentType<CardProps>;
}) {
  const { Row } = createCompetitionEntryComponents({
    squadVariant,
    imageVariant,
    useTranslation,
    Avatar,
    Link,
  });
  const { Card: ViewerCard } = createCompetitionViewerComponents({
    squadVariant,
    imageVariant,
    useTranslation,
    useSolPrice,
    Avatar,
    Link,
  });
  const { PrizeTier } = createCompetitionPrizeComponents({
    numberVariant,
    useTranslation,
  });
  const { findPrize } = createPrizeFormats({ numberVariant, Intl });
  return createCompetitionBoard({
    jsx,
    jsxs,
    React,
    useMemoCache,
    useTranslation,
    useReducedMotion,
    client,
    Hero,
    Highlights,
    Rules,
    Card,
    EntryRow: Row,
    ViewerCard,
    PrizeTier,
    findPrize,
    classNames: (...parts) => parts.filter(Boolean).join(" "),
  });
}
