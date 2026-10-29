import type {
  ComponentProps,
  ComponentType,
  Context,
  Provider,
  MouseEventHandler,
} from "react";
import type NextLink from "next/link";

export type ProfileIdentifier =
  | string
  | { address?: string | null; userId?: string | null }
  | null
  | undefined;
/** Client navigation/display capability only; never server authorization. */
export type ProfileNavigation = {
  pendingProfileId: ProfileIdentifier;
  navigateToProfile: (profileId: ProfileIdentifier) => void;
};
export type SourceProfileLinkProps = Omit<
  ComponentProps<typeof NextLink>,
  "href" | "onClick"
> & {
  profileId: ProfileIdentifier;
  href?: string;
  onClick?: MouseEventHandler<HTMLAnchorElement>;
};
export function profileRoute(profileId: ProfileIdentifier): string | null;
// Heterogeneous compiler cache slots have no recovered original TypeScript type.
export function useMemoCache(size: number): unknown[];
export function createProfileLinkModule(ports: {
  jsx: typeof import("react/jsx-runtime").jsx;
  useMemoCache: typeof useMemoCache;
  useContext: typeof import("react").useContext;
  createContext: (initial: null) => Context<ProfileNavigation | null>;
  Link: typeof NextLink;
  profileRoute: typeof profileRoute;
  classNames: (...classes: Array<string | false | undefined>) => string;
  isOrdinaryClick: (
    event: import("react").MouseEvent<HTMLAnchorElement>,
  ) => boolean;
}): {
  ProfileLink: ComponentType<SourceProfileLinkProps>;
  ProfileNavigationProvider: Provider<ProfileNavigation | null>;
};
