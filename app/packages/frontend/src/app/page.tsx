import Link from "next/link";
import { FeedList } from "@/components/feed/FeedList";
import { FeedTabs, type FeedTab } from "@/components/feed/FeedTabs";
import { NativeCalloutFeed } from "@/components/feed/NativeCalloutFeed";
import { loadLocalFeed } from "@/components/feed/feed-snapshot";
import { parseNativeFeedNavigation } from "@/components/feed/native-feed-navigation";
import {
  isNativeFeedEnabled,
  loadNativeFeed,
  type NativeFeedLoadResult,
} from "@/components/feed/native-feed-server";

type HomeSearchParams = {
  tab?: string | string[];
  nativeView?: string | string[];
  nativeCursor?: string | string[];
  nativeTrail?: string | string[];
};

function selectedTab(
  value: string | string[] | undefined,
  nativeEnabled: boolean,
): FeedTab {
  if (value === "local-callouts" && nativeEnabled) return "local-callouts";
  return value === "following" ? "following" : "for-you";
}
export default async function Home({
  searchParams,
}: {
  searchParams: Promise<HomeSearchParams>;
}) {
  const params = await searchParams;
  const nativeEnabled = isNativeFeedEnabled();
  const tab = selectedTab(params.tab, nativeEnabled);
  const localFeed = tab === "for-you" ? await loadLocalFeed() : null;
  let nativeNavigation: ReturnType<typeof parseNativeFeedNavigation> | null =
    null;
  let nativeResult: NativeFeedLoadResult | null = null;
  if (tab === "local-callouts") {
    try {
      nativeNavigation = parseNativeFeedNavigation(params);
      nativeResult = await loadNativeFeed(
        nativeNavigation.kind,
        nativeNavigation.cursor,
      );
    } catch {
      nativeNavigation = { kind: "ranked", trail: [] };
      nativeResult = {
        ok: false,
        reason: "invalid-cursor",
        message: "The local page navigation is malformed",
      };
    }
  }

  return (
    <div className="home-feed-page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Home</p>
          <h1>Feed</h1>
        </div>
        <Link className="page-heading-link" href="/explore">
          Explore coins →
        </Link>
      </div>

      <FeedTabs activeTab={tab} nativeEnabled={nativeEnabled} />

      <section
        id="home-feed-panel"
        className="home-feed-panel"
        role="tabpanel"
        aria-labelledby={`feed-tab-${tab}`}
        tabIndex={0}
      >
        {tab === "local-callouts" && nativeNavigation && nativeResult ? (
          <NativeCalloutFeed
            kind={nativeNavigation.kind}
            cursor={nativeNavigation.cursor}
            trail={nativeNavigation.trail}
            result={nativeResult}
          />
        ) : tab === "following" ? (
          <section
            className="feed-state-card"
            data-testid="following-unavailable"
          >
            <span className="feed-state-mark" aria-hidden="true">
              F
            </span>
            <h2>Following is unavailable offline</h2>
            <p>
              A personalized feed needs an authenticated viewer and a qualified
              follow graph. No followed users or posts are invented here.
            </p>
            <Link className="feed-state-link" href="/">
              Return to local examples
            </Link>
          </section>
        ) : !localFeed?.ok ? (
          <section className="feed-state-card" data-testid="local-feed-error">
            <span className="feed-state-mark" aria-hidden="true">
              !
            </span>
            <h2>Local example feed unavailable</h2>
            <p>
              The checked-in seed failed provenance or shape validation. No
              fallback posts or live network results were generated.
            </p>
          </section>
        ) : (
          <>
            <aside className="feed-provenance" aria-label="Feed data source">
              <strong>Local example data — not live Pump activity</strong>
              <span>
                {localFeed.dataset.posts.length} validated local posts from the
                hash-bound synthetic backend seed. External media stays offline.
              </span>
            </aside>
            <FeedList items={localFeed.dataset.posts} />
          </>
        )}
      </section>
    </div>
  );
}
