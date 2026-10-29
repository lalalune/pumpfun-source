// Full selected original controller; every acquisition/provider/browser capability is explicit.
function createPermissionPrompt(ports, useNotificationsContext) {
  const t = ports.jsxRuntime,
    i = { c: ports.memoCache },
    a = { K: ports.Button },
    n = { default: ports.Link },
    r = { f: ports.useTranslation },
    s = { f: ports.useAvailability },
    l = { y: useNotificationsContext };
  return (e) => {
    let o,
      c,
      d,
      m,
      u,
      p,
      f,
      x,
      g,
      h,
      b = (0, i.c)(27),
      { className: y } = e,
      { t: v } = (0, r.f)(),
      {
        permission: w,
        isConfigured: _,
        isRegistering: k,
        enablePushNotifications: j,
      } = (0, l.y)();
    if (!(0, s.f)() || !_ || "granted" === w || "unsupported" === w)
      return null;
    let C = `flex flex-col gap-3 rounded-xl border border-border-secondary bg-bg-secondary p-4 ${y ?? ""}`;
    return (
      b[0] !== v
        ? ((o = v("web.notification_settings.enable_browser_notifications")),
          (b[0] = v),
          (b[1] = o))
        : (o = b[1]),
      b[2] !== o
        ? ((c = (0, t.jsx)("p", {
            className: "text-sm font-semibold text-text-primary",
            children: o,
          })),
          (b[2] = o),
          (b[3] = c))
        : (c = b[3]),
      b[4] !== v
        ? ((d = v(
            "web.notification_settings.enable_browser_notifications_description",
          )),
          (b[4] = v),
          (b[5] = d))
        : (d = b[5]),
      b[6] !== d
        ? ((m = (0, t.jsx)("p", {
            className: "mt-1 text-sm text-text-secondary",
            children: d,
          })),
          (b[6] = d),
          (b[7] = m))
        : (m = b[7]),
      b[8] !== c || b[9] !== m
        ? ((u = (0, t.jsxs)("div", { children: [c, m] })),
          (b[8] = c),
          (b[9] = m),
          (b[10] = u))
        : (u = b[10]),
      b[11] !== j || b[12] !== k || b[13] !== w || b[14] !== v
        ? ((p =
            "default" === w
              ? (0, t.jsx)(a.K, {
                  isDisabled: k,
                  onClick: () => void j(),
                  size: 32,
                  variant: "primary",
                  children: v(
                    k
                      ? "web.notification_settings.enabling"
                      : "web.notification_settings.enable_notifications",
                  ),
                })
              : (0, t.jsx)("p", {
                  className: "text-sm text-text-secondary",
                  children: v("web.notification_settings.blocked_in_browser"),
                })),
          (b[11] = j),
          (b[12] = k),
          (b[13] = w),
          (b[14] = v),
          (b[15] = p))
        : (p = b[15]),
      b[16] !== v
        ? ((f = v("notifications.settings.title")), (b[16] = v), (b[17] = f))
        : (f = b[17]),
      b[18] !== f
        ? ((x = (0, t.jsx)(n.default, {
            className:
              "inline-flex h-9 items-center justify-center rounded-xl border border-border-secondary px-3 text-sm font-semibold text-text-primary hover:bg-bg-secondary",
            href: "/settings/notifications",
            children: f,
          })),
          (b[18] = f),
          (b[19] = x))
        : (x = b[19]),
      b[20] !== p || b[21] !== x
        ? ((g = (0, t.jsxs)("div", {
            className: "flex flex-wrap gap-2",
            children: [p, x],
          })),
          (b[20] = p),
          (b[21] = x),
          (b[22] = g))
        : (g = b[22]),
      b[23] !== C || b[24] !== g || b[25] !== u
        ? ((h = (0, t.jsxs)("div", { className: C, children: [u, g] })),
          (b[23] = C),
          (b[24] = g),
          (b[25] = u),
          (b[26] = h))
        : (h = b[26]),
      h
    );
  };
}
export function createNotificationsController(ports) {
  for (const name of [
    "memoCache",
    "useAvailability",
    "useFlag",
    "useAuthSnapshot",
    "useViewerKey",
    "usePathname",
    "useApiClient",
    "useQueryClient",
    "useMutation",
    "getConfigurationIndicator",
    "getDeviceHandle",
    "getMessagingHandle",
    "getRegistrationHandle",
    "removeRegistration",
    "onMessage",
    "foregroundMessage",
    "invalidateInbox",
    "reportError",
    "useTranslation",
  ])
    if (typeof ports?.[name] !== "function")
      throw new TypeError("Explicit notification capability required: " + name);
  for (const name of [
    "createContext",
    "useContext",
    "useState",
    "useRef",
    "useEffect",
    "useCallback",
  ])
    if (typeof ports.React?.[name] !== "function")
      throw new TypeError("Explicit React capability required: " + name);
  if (
    !["jsx", "jsxs"].every((n) => typeof ports.jsxRuntime?.[n] === "function")
  )
    throw new TypeError("Explicit JSX runtime required");
  if (
    !ports.browserFacade ||
    typeof ports.browserFacade !== "object" ||
    !Object.hasOwn(ports, "notificationFacade")
  )
    throw new TypeError("Explicit inert browser/Notification facades required");
  if (
    !["getItem", "setItem", "removeItem"].every(
      (n) => typeof ports.markerStorage?.[n] === "function",
    )
  )
    throw new TypeError("Explicit marker storage facade required");
  if (!ports.Button || !ports.Link)
    throw new TypeError(
      "Explicit source button/link rendering capabilities required",
    );
  const t = ports.jsxRuntime,
    n = { c: ports.memoCache },
    i = ports.React,
    r = { D: { WEB_DIRECT_MESSAGES: "webDirectMessages" } },
    a = { k: ports.useFlag },
    s = { useHermesApiClient: ports.useApiClient },
    l = { F: ports.useAuthSnapshot },
    o = { useQueryClient: ports.useQueryClient },
    u = { f: ports.useAvailability },
    d = { usePathname: ports.usePathname },
    f = { f: ports.useMutation },
    ei = { f: ports.useViewerKey },
    en = { l: ports.reportError },
    m = { O: ports.invalidateInbox },
    c = { onMessage: ports.onMessage };
  const w = ports.getConfigurationIndicator,
    g = ports.getDeviceHandle,
    S = ports.getMessagingHandle,
    U = ports.getRegistrationHandle,
    R = ports.removeRegistration,
    et = ports.foregroundMessage;
  const window = Object.create(ports.browserFacade),
    Notification = ports.notificationFacade;
  Object.defineProperty(window, "localStorage", { value: ports.markerStorage });
  let er = {
    permission: "unsupported",
    token: null,
    isRegistering: !1,
    isConfigured: !1,
  };
  let ea = "pump-push-token-owned";
  let es = (e) => {
    try {
      e
        ? window.localStorage.setItem(ea, "1")
        : window.localStorage.removeItem(ea);
    } catch {}
  };
  let el = (0, i.createContext)(null);
  const C = async () =>
    "Notification" in window
      ? "granted" === Notification.permission
        ? "granted"
        : "denied" === Notification.permission
          ? "denied"
          : Notification.requestPermission()
      : "denied";
  const Provider = (e) => {
    let p,
      h = (0, n.c)(3),
      { children: y } = e,
      x = (() => {
        let e,
          t,
          p,
          h = (0, u.f)(),
          y = (0, a.k)(r.D.WEB_DIRECT_MESSAGES),
          { fetchUser: x, authReady: v } = (0, l.F)(),
          b = (0, ei.f)("push-token"),
          _ = (0, d.usePathname)(),
          I = (0, s.useHermesApiClient)(),
          j = (0, o.useQueryClient)(),
          { mutateAsync: E } =
            ((t = (0, n.c)(2)),
            (p = (0, s.useHermesApiClient)()),
            t[0] !== p
              ? ((e = {
                  mutationFn: async (e) => {
                    if (!p)
                      throw Error("Hermes notifications API is not configured");
                    let t = { token: e, platform: "web", deviceId: g() };
                    await p.put("v1/device-tokens", { json: t });
                  },
                }),
                (t[0] = p),
                (t[1] = e))
              : (e = t[1]),
            (0, f.f)(e)),
          k = (0, i.useRef)(null),
          N = (0, i.useRef)(null),
          P = (0, i.useRef)(null),
          L = (0, i.useRef)(_),
          A = (0, i.useRef)(y);
        ((0, i.useEffect)(() => {
          L.current = _;
        }, [_]),
          (0, i.useEffect)(() => {
            A.current = y;
          }, [y]),
          (0, i.useEffect)(() => {
            !v ||
              null !== b ||
              ((N.current = null),
              (P.current = null),
              (() => {
                try {
                  return "1" === window.localStorage.getItem(ea);
                } catch {
                  return !1;
                }
              })() &&
                null !== w() &&
                (es(!1),
                O((e) => (null === e.token ? e : { ...e, token: null })),
                R().catch(() => void 0)));
          }, [v, b]));
        let [T, O] = (0, i.useState)(() => ({
            permission:
              "Notification" in window
                ? Notification.permission
                : "unsupported",
            token: null,
            isRegistering: !1,
            isConfigured: null !== w(),
          })),
          z = (0, i.useCallback)(async () => {
            if (!h || null === b || !I || null === w()) return null;
            O((e) => ({ ...e, isRegistering: !0 }));
            try {
              let e = await C();
              if ((O((t) => ({ ...t, permission: e })), "granted" !== e))
                return null;
              P.current &&
                P.current !== b &&
                N.current &&
                (await R().catch(() => void 0), (N.current = null));
              let t = await U();
              if (!t) return null;
              return (
                O((e) => (e.token === t ? e : { ...e, token: t })),
                (t !== N.current || P.current !== b) &&
                  (await E(t), (N.current = t), (P.current = b), es(!0)),
                t
              );
            } finally {
              O((e) => ({ ...e, isRegistering: !1 }));
            }
          }, [b, I, h, E]),
          B = (0, i.useCallback)(async () => (h ? z() : null), [h, z]);
        return ((0, i.useEffect)(() => {
          h &&
            null !== b &&
            I &&
            null !== w() &&
            "granted" === T.permission &&
            z().catch((e) => {
              (0, en.l)({
                error: e,
                feature: "notifications",
                operation: "register-token",
              });
            });
        }, [b, I, h, z, T.permission]),
        (0, i.useEffect)(() => {
          let e;
          if (!h || null === b || !I || !T.token || null === w()) return;
          let t = !1;
          return (
            S()
              .then((n) => {
                n &&
                  !t &&
                  ((k.current = n),
                  (e = (0, c.onMessage)(n, (e) => {
                    (et({
                      payload: e,
                      pathname: L.current,
                      hermesApi: I,
                      queryClient: j,
                      isDirectMessagesEnabled: A.current,
                    }),
                      (0, m.O)({ queryClient: j, viewer: b }),
                      x());
                  })));
              })
              .catch((e) => {
                (0, en.l)({
                  error: e,
                  feature: "notifications",
                  operation: "init-messaging",
                });
              }),
            () => {
              ((t = !0), e?.());
            }
          );
        }, [b, x, I, h, j, T.token]),
        h)
          ? { ...T, enablePushNotifications: B, registerCurrentToken: z }
          : { ...er, enablePushNotifications: B, registerCurrentToken: z };
      })();
    return (
      h[0] !== y || h[1] !== x
        ? ((p = (0, t.jsx)(el.Provider, { value: x, children: y })),
          (h[0] = y),
          (h[1] = x),
          (h[2] = p))
        : (p = h[2]),
      p
    );
  };
  const useNotificationsContext = () => {
    let e = (0, i.useContext)(el);
    if (!e)
      throw Error(
        "useNotificationsContext must be used within NotificationsProvider",
      );
    return e;
  };
  return {
    Provider,
    useNotificationsContext,
    PermissionPrompt: createPermissionPrompt(ports, useNotificationsContext),
    requestPermission: C,
  };
}
