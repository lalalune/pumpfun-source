import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
  useContext,
} from "../../packages/frontend/node_modules/react/index.js";
import { createRoot } from "../../packages/frontend/node_modules/react-dom/client.js";
import * as jsxRuntime from "../../packages/frontend/node_modules/react/jsx-runtime.js";
import { c } from "../../packages/frontend/node_modules/react/compiler-runtime.js";
import { createNotificationsController } from "../../reconstruction/notifications-controller/client.mjs";
const Scope = React.createContext(null),
  events = [],
  marker = new Map(),
  registrationCalls = [],
  apiCalls = [],
  messagingCalls = [],
  listeners = [];
let root,
  latest,
  latestValue,
  serial = 0,
  hostSerial = 0,
  patchScope,
  currentPermission = "default",
  permissionPending,
  configuration = true,
  regPlans = [],
  apiPlans = [],
  messagePlans = [];
const useScope = () => useContext(Scope);
const deferred = () => {
  let resolve, reject;
  const promise = new Promise((a, b) => {
    resolve = a;
    reject = b;
  });
  return { promise, resolve, reject };
};
const notification = {
  get permission() {
    events.push({ type: "permission-read", permission: currentPermission });
    return currentPermission;
  },
  requestPermission() {
    events.push({
      type: "permission-request",
      receiver: this === notification,
    });
    permissionPending = deferred();
    return permissionPending.promise;
  },
};
function planned(list, calls, type) {
  const plan = list.shift();
  if (!plan) throw Error("Unplanned synthetic port " + type);
  const id = calls.length + 1,
    d = deferred(),
    entry = { id, plan, deferred: d };
  calls.push(entry);
  events.push({ type: type + "-start", id });
  if (plan.reject) d.reject(Error(plan.reject));
  else if (Object.hasOwn(plan, "value")) d.resolve(plan.value);
  return d.promise.then((value) => {
    events.push({ type: type + "-fulfilled", id, hasValue: !!value });
    return value;
  });
}
const api = {
  put(path, options) {
    events.push({
      type: "api-put",
      path,
      keys: Object.keys(options.json),
      platform: options.json.platform,
      deviceIsSynthetic: options.json.deviceId === "synthetic-device-handle",
      registrationIsSynthetic:
        typeof options.json.token === "string" &&
        options.json.token.startsWith("synthetic-registration-"),
    });
    return planned(apiPlans, apiCalls, "api");
  },
};
const queryClient = { synthetic: true },
  refresh = () => events.push({ type: "refresh-user" }),
  translate = (key) =>
    key === "web.notification_settings.enable_notifications"
      ? "Enable synthetic notifications"
      : key;
const controller = createNotificationsController({
  React,
  jsxRuntime,
  memoCache: (n) => {
    events.push({ type: "memo", size: n });
    return c(n);
  },
  useAvailability: () => useScope().available,
  useFlag: (key) => {
    events.push({ type: "flag", key });
    return useScope().dm;
  },
  useAuthSnapshot: () => ({
    authReady: useScope().authReady,
    fetchUser: refresh,
  }),
  useViewerKey: (scope) => {
    events.push({ type: "viewer-scope", scope });
    return useScope().viewer;
  },
  usePathname: () => useScope().pathname,
  useApiClient: () => (useScope().apiAvailable ? api : null),
  useQueryClient: () => queryClient,
  // Explicit synthetic query-hook result port, not a TanStack implementation.
  useMutation: (options) => {
    const ref = useRef(options);
    ref.current = options;
    const mutateAsync = useCallback(
      (value) => ref.current.mutationFn(value),
      [],
    );
    return { mutateAsync };
  },
  getConfigurationIndicator: () => {
    events.push({ type: "configuration-check", available: configuration });
    return configuration ? {} : null;
  },
  getDeviceHandle: () => {
    events.push({ type: "device-port" });
    return "synthetic-device-handle";
  },
  getMessagingHandle: () => planned(messagePlans, messagingCalls, "messaging"),
  getRegistrationHandle: () =>
    planned(regPlans, registrationCalls, "registration"),
  removeRegistration: async () => {
    events.push({ type: "remove-registration" });
  },
  onMessage: (handle, callback) => {
    const listener = { callback, active: true, id: listeners.length + 1 };
    listeners.push(listener);
    events.push({ type: "listener-install", id: listener.id });
    return () => {
      listener.active = false;
      events.push({ type: "listener-cleanup", id: listener.id });
    };
  },
  foregroundMessage: (options) => {
    events.push({
      type: "foreground",
      pathname: options.pathname,
      dm: options.isDirectMessagesEnabled,
      hasPayload: !!options.payload,
      clientMatches: options.hermesApi === api,
      queryClientMatches: options.queryClient === queryClient,
    });
    return new Promise(() => {});
  },
  invalidateInbox: (options) =>
    events.push({
      type: "invalidate-inbox",
      viewer: options.viewer,
      queryClientMatches: options.queryClient === queryClient,
    }),
  reportError: (options) =>
    events.push({
      type: "report-error",
      feature: options.feature,
      operation: options.operation,
    }),
  useTranslation: () => ({ t: translate }),
  browserFacade: { Notification: notification },
  notificationFacade: notification,
  markerStorage: {
    getItem(key) {
      events.push({ type: "marker-get", key });
      return marker.get(key) ?? null;
    },
    setItem(key, value) {
      events.push({ type: "marker-set", key, value });
      marker.set(key, value);
    },
    removeItem(key) {
      events.push({ type: "marker-remove", key });
      marker.delete(key);
    },
  },
  Button: ({ isDisabled, onClick, children }) =>
    React.createElement("button", { disabled: isDisabled, onClick }, children),
  Link: ({ href, children }) => React.createElement("a", { href }, children),
});
const initialScope = {
  available: true,
  dm: true,
  authReady: true,
  viewer: "synthetic-viewer-a",
  pathname: "/before",
  apiAvailable: true,
};
function Consumer() {
  const value = controller.useNotificationsContext();
  latestValue = value;
  useEffect(() => {
    latest = {
      permission: value.permission,
      hasRegistration: !!value.token,
      isRegistering: value.isRegistering,
      isConfigured: value.isConfigured,
    };
    serial++;
    events.push({ type: "commit", serial, state: latest });
  });
  return React.createElement(
    React.Fragment,
    null,
    React.createElement(
      "output",
      { id: "state" },
      JSON.stringify({
        permission: value.permission,
        isRegistering: value.isRegistering,
      }),
    ),
    React.createElement(controller.PermissionPrompt, {}),
  );
}
function App({ scope }) {
  const [current, setCurrent] = useState(scope);
  patchScope = (patch) => setCurrent((s) => ({ ...s, ...patch }));
  useEffect(() => {
    hostSerial++;
    events.push({ type: "host-commit", serial: hostSerial });
  });
  return React.createElement(
    Scope.Provider,
    { value: current },
    React.createElement(controller.Provider, {}, React.createElement(Consumer)),
  );
}
function mount(scope = initialScope) {
  latest = null;
  root = createRoot(document.getElementById("root"));
  root.render(React.createElement(App, { scope }));
}
function release(calls, id, value) {
  const call = calls[id - 1];
  if (!call) throw Error("Unknown synthetic call");
  call.deferred.resolve(value);
  return call.deferred.promise
    .then(() => Promise.resolve())
    .then(() => Promise.resolve());
}
window.notificationHarness = {
  state: () => structuredClone(latest),
  events: () => structuredClone(events),
  serial: () => serial,
  hostSerial: () => hostSerial,
  scope: (patch) => patchScope(patch),
  counts: () => ({
    registration: registrationCalls.length,
    api: apiCalls.length,
    messaging: messagingCalls.length,
    installed: listeners.length,
    active: listeners.filter((l) => l.active).length,
    markerOwned: marker.get("pump-push-token-owned") === "1",
  }),
  plan: (kind, plans) => {
    if (kind === "registration") regPlans.push(...plans);
    else if (kind === "api") apiPlans.push(...plans);
    else if (kind === "messaging") messagePlans.push(...plans);
    else throw Error("Unknown plan kind");
  },
  grant: (value) => {
    currentPermission = value;
    permissionPending.resolve(value);
  },
  releaseRegistration: (id, value) => release(registrationCalls, id, value),
  releaseApi: (id) => release(apiCalls, id, undefined),
  releaseMessaging: (id) =>
    release(messagingCalls, id, { syntheticMessaging: true }),
  register: async () => {
    const value = await latestValue.registerCurrentToken();
    return {
      hasResult: !!value,
      resultIsSynthetic:
        value === null ||
        (typeof value === "string" &&
          value.startsWith("synthetic-registration-")),
    };
  },
  enable: async () => {
    const value = await latestValue.enablePushNotifications();
    return { hasResult: !!value };
  },
  emit: () => {
    const listener = listeners.findLast((l) => l.active);
    if (!listener) throw Error("No synthetic listener");
    listener.callback({ data: { synthetic: true } });
  },
  reset: (options) => {
    root.unmount();
    marker.clear();
    regPlans = [];
    apiPlans = [];
    messagePlans = [];
    currentPermission = options.permission ?? "granted";
    configuration = options.configuration ?? true;
    regPlans.push(...(options.registration ?? []));
    apiPlans.push(...(options.api ?? []));
    messagePlans.push(...(options.messaging ?? []));
    mount({ ...initialScope, ...options.scope });
  },
  unmount: () => root.unmount(),
};
mount();
