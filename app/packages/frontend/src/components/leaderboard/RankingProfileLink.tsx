"use client";

import Link from "next/link";
import { createContext, useContext, type ReactNode } from "react";
import { jsx } from "react/jsx-runtime";
import {
  createProfileLinkModule,
  profileRoute,
  useMemoCache,
  type ProfileNavigation,
} from "./original-profile-link.mjs";
import { isOrdinaryClick } from "./original-profile-click.mjs";

const { ProfileLink } = createProfileLinkModule({
  jsx,
  useMemoCache,
  useContext,
  createContext: (initial) => createContext<ProfileNavigation | null>(initial),
  Link,
  profileRoute,
  isOrdinaryClick,
  // Local port for the actual fixed class set; original Tailwind merger parity
  // is not claimed. The private navigation provider remains absent/null.
  classNames: (...classes) => classes.filter(Boolean).join(" "),
});

export function RankingProfileLink({
  identifier,
  label,
  children,
}: {
  identifier: string;
  label: string;
  children: ReactNode;
}) {
  return (
    <ProfileLink
      profileId={identifier}
      prefetch={false}
      className="hover:underline"
      title="View the matching local synthetic example profile"
      aria-label={`View local example profile for ${label}`}
    >
      {children}
    </ProfileLink>
  );
}
