# Original Notifications control frame

This restores the complete selected `32596.Q/y` provider/context frame, its
browser-permission decision and `979364` permission prompt. The actual settings
consumer `917781` and provider mount in `589428` are source witnesses. Their
surrounding settings/auth-root implementations are not reconstructed here.
The prior foreground notification unit explicitly leaves this outer
registration/listener lifecycle outside its scope.

The generator authenticates the physical factories, original UTF-16/UTF-8 ranges
and complete selected functions. Emitted provider, context reader, permission
helper, defaults, ownership marker/context declarations and full prompt compare
as strict ASTs: only parser positions/comments/raw spelling metadata are ignored.
There is no alpha/type/operation masking or captured-module execution. The
editable module and JSON contract are checked as exact canonical bytes.

## Explicit capabilities only

`createNotificationsController(ports)` returns `Provider`,
`useNotificationsContext`, `PermissionPrompt` and `requestPermission`.
It requires real React/JSX/compiler capabilities and all listed functions. It
has no fallback to the browser, configuration, auth, storage or network. One
adapter instance represents one original module/context instance.

| Port                                                                             | Actual selected boundary                                                                                                                                                                                                                          |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `React`, `jsxRuntime`, `memoCache(size)`                                         | Explicit framework capabilities; provider/mutation/prompt memo frames are retained.                                                                                                                                                               |
| `useAvailability()`, `useFlag(name)`                                             | Supplied feature snapshots. DM flag name is the captured `webDirectMessages`. No feature service is implemented.                                                                                                                                  |
| `useAuthSnapshot()`                                                              | Supplied `{authReady, fetchUser}`; no session/account acquisition.                                                                                                                                                                                |
| `useViewerKey(scope)`                                                            | Actual scope is `push-token`; supplies an identity key or null. This is not credential acquisition.                                                                                                                                               |
| `usePathname()`, `useApiClient()`, `useQueryClient()`                            | Opaque read-only router/client/query snapshots. The client is supplied or null, not constructed here.                                                                                                                                             |
| `useMutation({mutationFn})`                                                      | Opaque actual query-hook result `{mutateAsync}`. TanStack scheduling/retries/error policy remain external.                                                                                                                                        |
| `getConfigurationIndicator()`                                                    | Supplies null or a nonnull opaque indicator. Only nullness is consumed; no environment/configuration values are acquired.                                                                                                                         |
| `getDeviceHandle()`                                                              | Supplies a string to the source request builder. Tests use explicitly synthetic noncredential values.                                                                                                                                             |
| `getRegistrationHandle()`, `removeRegistration()`                                | Supplied Promise results. No Firebase/token/subscription/deletion implementation or real values.                                                                                                                                                  |
| `getMessagingHandle()`, `onMessage(handle, callback)`                            | Supplied opaque handle and callback installer returning cleanup. No actual messaging subscription.                                                                                                                                                |
| `foregroundMessage(options)`, `invalidateInbox(options)`, `reportError(options)` | Required source-shaped callbacks. The existing foreground/inbox/Hermes work is credited and unchanged, not reimplemented.                                                                                                                         |
| `browserFacade`, `notificationFacade`, `markerStorage`                           | Inert availability/Notification facade and Storage-shaped selected-marker methods. `notificationFacade` must be explicitly supplied, including undefined for unsupported. Never supply actual browser/service/storage capabilities in proof runs. |
| `useTranslation()`, `Button`, `Link`                                             | Explicit prompt rendering dependencies. Original button/link/translation/provider behavior remains external.                                                                                                                                      |

`browserFacade` controls only the source `'Notification' in window` admission;
the separate stable Notification facade supplies `permission` and
`requestPermission()`. The adapter's local window inherits that inert facade and
uses the supplied `markerStorage` exclusively. Neither real global API nor real
storage is read. Constructor capability checks are local adapter admission,
not a recovered whole browser/provider API.

The proof renderer's button/link adapters and supplied results are synthetic
host capabilities, not product components or original provider implementations.
Nothing here enables browser push in the maintained application. The twelve
previously captured configurations still have Hermes disabled; current feature,
configuration, provider and authorization availability remain unknown.

## Preserved source behavior and limits

- Permission helper returns denied when unsupported, returns granted/denied
  directly from those values, otherwise calls the supplied request method with
  its receiver. It retains repeated getter reads and Promise rejection.
- The provider initializes permission/configured state, but a disabled feature
  exposes the original unsupported/empty defaults with its callbacks. It does
  not infer a current permission or configured account from local settings.
- Registration checks feature/viewer/client/configuration, sets the busy flag,
  obtains permission, clears changed-viewer registration refs as written and
  obtains a supplied handle. It publishes that handle **before** awaiting the
  source client mutation. Only successful mutation commits equality refs and
  the owned-marker flag. `finally` clears a boolean busy flag, not a count.
- The mutation callback builds `{token, platform: 'web', deviceId}` and awaits
  `client.put('v1/device-tokens', {json: ...})`, ignoring the response. The client
  is an explicit port. No HTTP request, serialization/auth contract or token
  service is implemented or exercised by this unit's proof host.
- Preserve actual equality-based deduplication after refs commit. There is no
  new in-flight lock: overlapping manual/automatic calls can occur. A failure
  can leave handle state populated, and registration continuation has no added
  unmount cancellation. No registration/ownership/security guarantee is inferred.
- Path/DM flag refs update independently. Messaging initialization checks its
  guards, skips a late result after effect cleanup and unsubscribes the installed
  callback. The received callback invokes foreground handling, inbox invalidation
  and user refresh in that order without awaiting them. It does not implement
  their backend/provider/UI effects. Bridge the existing foreground adapter
  using its documented constructor capabilities and these per-call arguments.
- On auth-ready/null-viewer reset, refs clear before the selected owned marker
  is read. Marker/configuration admission then clears marker/handle and requests
  supplied cleanup. This reset does not add a feature-availability guard.
- Prompt display and offered enable action retain the original feature,
  configured, permission and registering gates. This is editable source and
  synthetic rendering proof, not mounted settings/push/visual compatibility.

No actual credentials, configuration/environment values, cookie/session/token
values, device IDs, real storage, Notification API, Firebase, service worker,
network request, subscription, wallet action or notification is acquired/read/
requested. Tests use inert facades and explicitly synthetic noncredential
strings/results only. The acquisition helpers are retained as source witnesses,
not copied or executed implementations.

## Repeat

From `app/`, with pinned installed dependencies and an existing Chromium:

```sh
node scripts/original-notifications-controller.mjs --check
node --test tests/original_notifications_controller.test.mjs
node --test tests/original_notifications_controller.browser.mjs
```

The last command bundles the maintained adapter and a synthetic real React host.
An ephemeral loopback server serves only the root and bundle; all provider/client
operations are inert supplied callbacks, with no provider HTTP request. Optional
`PUMP_NOTIFICATION_CONTROLLER_OUTPUT` saves observations/input hashes and
`PUMP_BROWSER_EXECUTABLE` selects an existing executable. It closes browser/host
on completion; there is no Next server, installation or product fixture.

Full auth/provider/query/browser lifecycle equivalence, live push delivery,
backend persistence/authorization/native/API compatibility, visual/security
equivalence and feature-completion milestones remain unqualified. Captures,
SDK, shared source/graph code and earlier packets remain unchanged.
