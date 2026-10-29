/** Static UI labels derived from recovered factories; never account preferences. */
export const SETTINGS_SECTIONS = [
  { id: "trading", label: "Trading" },
  { id: "chart", label: "Chart" },
  { id: "feed", label: "Feed" },
  { id: "notifications", label: "Notifications" },
  { id: "account", label: "Account" },
  { id: "display", label: "Display" },
  { id: "privacy", label: "Privacy" },
] as const;

export type SettingsSection = (typeof SETTINGS_SECTIONS)[number]["id"];
export type SettingDefinition = {
  id: string;
  section: SettingsSection;
  group: string;
  label: string;
  description: string;
  searchTerms: readonly string[];
};

// Notification labels describe captured translation keys. The three general
// settings and section labels are bound to captured English resources in the
// settings-notifications contract. No fallback boolean is a user value.
export const SETTINGS_DEFINITIONS: readonly SettingDefinition[] = [
  {
    id: "notifications.browserPush",
    section: "notifications",
    group: "Browser push",
    label: "Browser notifications",
    description:
      "Browser permission and push registration are not connected. No permission request will be made.",
    searchTerms: ["push", "permission", "device"],
  },
  {
    id: "social.allowDmMessageNotifications",
    section: "notifications",
    group: "Chat",
    label: "Direct messages",
    description: "Notifications for direct messages.",
    searchTerms: ["dm", "chat", "inbox"],
  },
  {
    id: "chat.allowGroupNotifications",
    section: "notifications",
    group: "Chat",
    label: "Group chats",
    description: "Notifications for group conversations.",
    searchTerms: ["messages", "group"],
  },
  {
    id: "chat.allowChatRequestNotifications",
    section: "notifications",
    group: "Chat",
    label: "Chat requests",
    description: "Notifications for new chat requests.",
    searchTerms: ["messages", "request"],
  },
  {
    id: "social.allowFollowerNotifications",
    section: "notifications",
    group: "Social",
    label: "New followers",
    description: "Notifications when someone follows your account.",
    searchTerms: ["follow", "social"],
  },
  {
    id: "social.allowNewCoinNotifications",
    section: "notifications",
    group: "Social",
    label: "New coins from follows",
    description: "Notifications about coins created by accounts you follow.",
    searchTerms: ["follow", "creation", "coin"],
  },
  {
    id: "social.allowCoinWatcherNotifications",
    section: "notifications",
    group: "Social",
    label: "Bookmarked coin updates",
    description: "Notifications about coins you have bookmarked.",
    searchTerms: ["watcher", "social", "bookmark"],
  },
  {
    id: "coins.allowPriceSpikeNotifications",
    section: "notifications",
    group: "Coins",
    label: "Price spikes",
    description: "Notifications about coin price spikes.",
    searchTerms: ["price", "coin"],
  },
  {
    id: "coins.allowLiveStreamNotifications",
    section: "notifications",
    group: "Coins",
    label: "Livestreams",
    description: "Notifications when coin livestreams start.",
    searchTerms: ["live", "stream"],
  },
  {
    id: "coins.allowCalloutNotifications",
    section: "notifications",
    group: "Coins",
    label: "Callouts",
    description: "Notifications about coin callouts.",
    searchTerms: ["callout", "coin"],
  },
  {
    id: "topics.trending",
    section: "notifications",
    group: "Trending topics",
    label: "Trending livestreams",
    description:
      "The captured trending topic subscription. Subscription status is unavailable.",
    searchTerms: ["trending", "live"],
  },
  {
    id: "topics.trending_searches",
    section: "notifications",
    group: "Trending topics",
    label: "Popular coins · more updates",
    description:
      "The captured trending_searches topic. Subscription status is unavailable.",
    searchTerms: ["trending", "popular", "heavy"],
  },
  {
    id: "topics.quiet_trending_searches",
    section: "notifications",
    group: "Trending topics",
    label: "Popular coins · fewer updates",
    description:
      "The captured quiet_trending_searches topic. Subscription status is unavailable.",
    searchTerms: ["trending", "popular", "light"],
  },
  {
    id: "account.hidePersonalInfo",
    section: "account",
    group: "Privacy",
    label: "Hide your email and wallet address",
    description:
      "Mask your email and wallet address on your own profile, for streaming or screenshots.",
    searchTerms: ["eyeball", "privacy", "stream", "mask", "email", "address"],
  },
  {
    id: "display.language",
    section: "display",
    group: "Language",
    label: "Language",
    description: "Choose the language the pump.fun interface is displayed in.",
    searchTerms: ["language", "locale", "translation", "english"],
  },
  {
    id: "privacy.confirmExternalLinks",
    section: "privacy",
    group: "External links",
    label: "Confirm before opening external links",
    description: "Show a warning before a link takes you off pump.fun.",
    searchTerms: ["external links", "leaving", "warning", "don't ask again"],
  },
];

export function isSettingsSection(value: string): value is SettingsSection {
  return SETTINGS_SECTIONS.some((section) => section.id === value);
}

export function readSettingsLocation(params: URLSearchParams): {
  section: SettingsSection | null;
  settingId: string | null;
} {
  const values = params.getAll("settings");
  if (values.length !== 1 || !isSettingsSection(values[0])) {
    return { section: null, settingId: null };
  }
  const section = values[0];
  const targets = params.getAll("setting");
  const settingId =
    targets.length === 1 &&
    SETTINGS_DEFINITIONS.some(
      (setting) => setting.id === targets[0] && setting.section === section,
    )
      ? targets[0]
      : null;
  return { section, settingId };
}

/** Keeps unrelated repeated query parameters and fragment; consumes only our keys. */
export function settingsHref(
  pathname: string,
  params: URLSearchParams,
  section: SettingsSection | null,
  hash = "",
): string {
  // Callers use usePathname(); reject external and script URLs defensively.
  if (
    !pathname.startsWith("/") ||
    pathname.startsWith("//") ||
    /[\u0000-\u001f\u007f?#\\]/.test(pathname)
  ) {
    throw new Error("Expected a same-origin pathname");
  }
  const next = new URLSearchParams(params);
  next.delete("settings");
  next.delete("setting");
  if (section !== null) {
    if (!isSettingsSection(section))
      throw new Error("Unknown settings section");
    next.set("settings", section);
  }
  const query = next.toString();
  return `${pathname}${query ? `?${query}` : ""}${hash.startsWith("#") ? hash : ""}`;
}

export function normalizeSettingsSearch(value: string): string {
  return value
    .trim()
    .toLocaleLowerCase("en")
    .normalize("NFKD")
    .replace(/\p{M}/gu, "");
}

export function findSettings(query: string): readonly SettingDefinition[] {
  const normalized = normalizeSettingsSearch(query);
  if (!normalized) return [];
  const terms = normalized.split(/\s+/);
  return SETTINGS_DEFINITIONS.filter((setting) => {
    const text = normalizeSettingsSearch(
      [
        setting.label,
        setting.description,
        setting.group,
        setting.section,
        ...setting.searchTerms,
        setting.id.replace(/[.]/g, " "),
      ].join(" "),
    );
    return terms.every((term) => text.includes(term));
  });
}
