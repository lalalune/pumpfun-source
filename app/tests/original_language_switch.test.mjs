import { test } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { once } from "node:events";
import { createRequire } from "node:module";
import { verify } from "../scripts/original-language-switch.mjs";
import {
  createLocaleCatalog,
  createLocaleCookie,
  createLanguageClient,
  createLanguageSelector,
} from "../reconstruction/language-switch/client.mjs";

const frontend = createRequire(
  new URL("../packages/frontend/package.json", import.meta.url),
);
const React = frontend("react"),
  jsx = frontend("react/jsx-runtime");
const { renderToString } = frontend("react-dom/server");
const { c: useMemoCache } = frontend("react/compiler-runtime");
const catalog = createLocaleCatalog();
const deferred = () => {
  let resolve;
  const promise = new Promise((r) => {
    resolve = r;
  });
  return { promise, resolve };
};
function cookiePort({
  initial = "",
  protocol = "https:",
  fail = false,
  log = [],
} = {}) {
  let value = initial;
  const document = {};
  Object.defineProperty(document, "cookie", {
    get: () => value,
    set: (next) => {
      log.push(["cookie", next]);
      if (fail) throw Error("synthetic cookie denied");
      value = next;
    },
  });
  return {
    ...createLocaleCookie({
      document,
      location: { protocol },
      normalizeLocale: catalog.normalizeLocale,
    }),
    current: () => value,
  };
}
function instance(log = [], { reject = false, gate } = {}) {
  const resources = new Map();
  return {
    language: "en",
    resources,
    getResource(locale, namespace, key) {
      log.push(["getResource", locale, namespace, key]);
      return resources.get(locale)?.[key];
    },
    addResourceBundle(locale, namespace, value, deep, overwrite) {
      log.push(["bundle", locale, namespace, value, deep, overwrite]);
      resources.set(locale, { ...resources.get(locale), ...value });
    },
    async changeLanguage(locale) {
      log.push(["change:start", locale]);
      if (gate) await gate;
      if (reject) throw Error("synthetic language change denied");
      this.language = locale;
      log.push(["change:end", locale]);
    },
  };
}
async function http(handler) {
  const requests = [];
  const server = createServer(async (request, response) => {
    requests.push({ method: request.method, url: request.url });
    if (request.method !== "GET") {
      response.writeHead(405).end();
      return;
    }
    try {
      const result = await handler(
        new URL(request.url, "http://owned.invalid"),
      );
      response.writeHead(result.status ?? 200, {
        "Content-Type": "application/json",
      });
      response.end(result.raw ?? JSON.stringify(result.body));
    } catch {
      response.writeHead(500).end();
    }
  });
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const base = "http://127.0.0.1:" + server.address().port;
  return {
    requests,
    fetch: (url, init) => {
      assert.ok(url.startsWith("/api/i18n/"));
      assert.equal(init, undefined);
      return fetch(new URL(url, base));
    },
    close: () => new Promise((resolve) => server.close(resolve)),
  };
}
function client(transport, log = [], cookie = cookiePort({ log })) {
  return createLanguageClient({
    fetch: transport.fetch,
    logger: { warn: (...args) => log.push(["warn", ...args]) },
    writeCookie: cookie.writeCookie,
  });
}

test("source gate binds complete language export, exact namespace client and custom field bypass", async () => {
  const contract = await verify();
  assert.equal(contract.provenance.length, 7);
  assert.equal(contract.retained.length, 17);
  assert.equal(contract.callerWitnesses.length, 5);
  assert.ok(contract.selectorNamespaces.includes("web.settings"));
  assert.equal(
    contract.limits.some((value) => value.includes("749099 is excluded")),
    true,
  );
});

test("complete 35-locale metadata/order and original alias/prefix normalization are preserved", () => {
  assert.equal(catalog.locales.length, 35);
  assert.equal(catalog.defaultLocale, "en");
  assert.equal(catalog.locales[0], "en");
  assert.equal(catalog.metadata.fr.label, "Français");
  assert.equal(catalog.metadata.nb.flag, "🇳🇴");
  for (const value of ["no", "NO-no", " nb-NO "])
    assert.equal(catalog.normalizeLocale(value), "nb");
  assert.equal(catalog.normalizeLocale("ZH-hant"), "zh");
  for (const value of [undefined, null, "", " ", "unknown", "xx-yy"])
    assert.equal(catalog.normalizeLocale(value), null);
  assert.throws(() => catalog.normalizeLocale(7), TypeError); // No invented input coercion.
});

test("explicit synthetic cookie parser keeps first match, URI decoding and malformed-value throws", () => {
  const port = cookiePort({
    initial: "other=x; pump_locale=%6e%6f-NO; tail=x",
  });
  assert.equal(port.readCookie(), "nb");
  assert.equal(port.parseHeader("pump_locale=unknown; pump_locale=fr"), null);
  assert.equal(port.parseHeader("pump_locale =fr"), null);
  assert.equal(port.parseHeader(""), null);
  assert.throws(() => port.parseHeader("pump_locale=%"), URIError);
});

test("cookie writer uses exact protocol-sensitive attributes and no implicit document", () => {
  const secure = cookiePort();
  secure.writeCookie("fr");
  assert.equal(
    secure.current(),
    "pump_locale=fr; path=/; max-age=31536000; samesite=lax; secure",
  );
  const local = cookiePort({ protocol: "http:" });
  local.writeCookie("en");
  assert.equal(
    local.current(),
    "pump_locale=en; path=/; max-age=31536000; samesite=lax",
  );
  const absent = createLocaleCookie({
    document: undefined,
    location: undefined,
    normalizeLocale: catalog.normalizeLocale,
  });
  assert.equal(absent.readCookie(), null);
  assert.equal(absent.writeCookie("fr"), undefined);
});

test("real loopback full-catalog load precedes cookie, awaited change and router refresh", async () => {
  const log = [],
    gate = deferred(),
    i18n = instance(log, { gate: gate.promise });
  const transport = await http(() => ({
    body: { "web.settings": { synthetic: true } },
  }));
  try {
    const service = client(transport, log);
    const running = service.changeLanguage({
      instance: i18n,
      locale: "fr",
      namespaces: ["web.settings"],
      router: { refresh: () => log.push(["refresh"]) },
    });
    while (!log.some((entry) => entry[0] === "change:start"))
      await new Promise((r) => setTimeout(r, 1));
    assert.equal(
      log.some((entry) => entry[0] === "refresh"),
      false,
    );
    assert.ok(
      log.findIndex((entry) => entry[0] === "cookie") <
        log.findIndex((entry) => entry[0] === "change:start"),
    );
    gate.resolve();
    await running;
    assert.deepEqual(
      log
        .filter((entry) =>
          ["cookie", "change:start", "change:end", "refresh"].includes(
            entry[0],
          ),
        )
        .map((entry) => entry[0]),
      ["cookie", "change:start", "change:end", "refresh"],
    );
    assert.deepEqual(transport.requests, [
      { method: "GET", url: "/api/i18n/fr?ns=__all__" },
    ]);
    assert.deepEqual(log.find((entry) => entry[0] === "bundle").slice(-2), [
      true,
      true,
    ]);
  } finally {
    gate.resolve();
    await transport.close();
  }
});

test("full-catalog HTTP failure warns, retries later, and successful namespace fallback still switches", async () => {
  const log = [],
    i18n = instance(log);
  let catalogs = 0;
  const transport = await http((url) =>
    url.searchParams.get("ns") === "__all__"
      ? ++catalogs === 1
        ? { status: 503, raw: "not JSON" }
        : { body: { common: { synthetic: true } } }
      : { body: { common: { synthetic: true } } },
  );
  try {
    const service = client(transport, log),
      router = { refresh: () => log.push(["refresh"]) };
    await service.changeLanguage({
      instance: i18n,
      locale: "fr",
      namespaces: ["common"],
      router,
    });
    assert.equal(log.filter((entry) => entry[0] === "warn").length, 1);
    assert.match(
      log.find((entry) => entry[0] === "warn")[1],
      /idle full-catalog/,
    );
    assert.equal(i18n.language, "fr");
    await service.changeLanguage({
      instance: i18n,
      locale: "fr",
      namespaces: ["common"],
      router,
    });
    assert.equal(catalogs, 2);
    assert.deepEqual(
      transport.requests.map((entry) => entry.url),
      [
        "/api/i18n/fr?ns=__all__",
        "/api/i18n/fr?ns=common",
        "/api/i18n/fr?ns=__all__",
      ],
    );
  } finally {
    await transport.close();
  }
});

test("namespace HTTP failure warns but cookie/change/refresh still run in source order", async () => {
  const log = [],
    i18n = instance(log);
  const transport = await http((url) =>
    url.searchParams.get("ns") === "__all__"
      ? { body: {} }
      : { status: 502, raw: "not JSON" },
  );
  try {
    await client(transport, log).changeLanguage({
      instance: i18n,
      locale: "de",
      namespaces: ["missing"],
      router: { refresh: () => log.push(["refresh"]) },
    });
    assert.deepEqual(
      log
        .filter((entry) =>
          ["warn", "cookie", "change:start", "change:end", "refresh"].includes(
            entry[0],
          ),
        )
        .map((entry) => entry[0]),
      ["warn", "cookie", "change:start", "change:end", "refresh"],
    );
    assert.match(
      log.find((entry) => entry[0] === "warn")[2].reason,
      /i18n namespace fetch failed: 502/,
    );
  } finally {
    await transport.close();
  }
});

test("namespace loader selects only falsy/missing resources and preserves query encoding/order", async () => {
  const log = [],
    i18n = instance(log);
  i18n.resources.set("fr", { existing: { yes: true }, falsy: false });
  const transport = await http(() => ({ body: { seeded: true } }));
  try {
    await client(transport, log).seedNamespaces(i18n, "fr", [
      "existing",
      "falsy",
      "web.settings",
    ]);
    assert.deepEqual(transport.requests, [
      { method: "GET", url: "/api/i18n/fr?ns=falsy%2Cweb.settings" },
    ]);
    await client(transport, log).seedNamespaces(i18n, "fr", ["existing"]);
    assert.equal(transport.requests.length, 1);
  } finally {
    await transport.close();
  }
});

test("cache is per instance/locale and successful full prefetch avoids another GET", async () => {
  const transport = await http(() => ({ body: { common: true } }));
  try {
    const service = client(transport),
      first = instance(),
      second = instance();
    await service.prefetchCatalog(first, "fr");
    await service.prefetchCatalog(first, "fr");
    await service.prefetchCatalog(first, "de");
    await service.prefetchCatalog(second, "fr");
    assert.equal(transport.requests.length, 3);
  } finally {
    await transport.close();
  }
});

test("mark-before-await cache skips a concurrent caller rather than waiting for the first fetch", async () => {
  const reached = deferred(),
    release = deferred();
  const transport = await http(async () => {
    reached.resolve();
    await release.promise;
    return { body: {} };
  });
  try {
    const service = client(transport),
      i18n = instance();
    const first = service.prefetchCatalog(i18n, "fr");
    await reached.promise;
    let secondDone = false;
    await service.prefetchCatalog(i18n, "fr").then(() => {
      secondDone = true;
    });
    assert.equal(secondDone, true);
    assert.equal(transport.requests.length, 1);
    release.resolve();
    await first;
  } finally {
    release.resolve();
    await transport.close();
  }
});

test("failed JSON decode deletes prefetch cache and retains formatted synthetic warning", async () => {
  const log = [],
    i18n = instance();
  const transport = await http(() => ({ raw: "{" }));
  try {
    const service = client(transport, log);
    await service.prefetchCatalog(i18n, "fr");
    await service.prefetchCatalog(i18n, "fr");
    assert.equal(transport.requests.length, 2);
    assert.equal(log.filter((entry) => entry[0] === "warn").length, 2);
    assert.match(log[0][2].reason, /^SyntaxError:/);
  } finally {
    await transport.close();
  }
});

test("changeLanguage rejection leaves prior cookie write and skips refresh; rejection propagates", async () => {
  const log = [],
    i18n = instance(log, { reject: true });
  const transport = await http(() => ({ body: {} }));
  try {
    const port = cookiePort({ log });
    await assert.rejects(
      client(transport, log, port).changeLanguage({
        instance: i18n,
        locale: "fr",
        namespaces: [],
        router: { refresh: () => log.push(["refresh"]) },
      }),
      /synthetic language change denied/,
    );
    assert.match(port.current(), /^pump_locale=fr;/);
    assert.equal(i18n.language, "en");
    assert.equal(
      log.some((entry) => entry[0] === "refresh"),
      false,
    );
  } finally {
    await transport.close();
  }
});

test("cookie-port error propagates before provider change/refresh", async () => {
  const log = [],
    i18n = instance(log);
  const transport = await http(() => ({ body: {} }));
  try {
    const port = cookiePort({ fail: true, log });
    await assert.rejects(
      client(transport, log, port).changeLanguage({
        instance: i18n,
        locale: "fr",
        namespaces: [],
        router: { refresh: () => log.push(["refresh"]) },
      }),
      /synthetic cookie denied/,
    );
    assert.equal(
      log.some(
        (entry) => entry[0] === "change:start" || entry[0] === "refresh",
      ),
      false,
    );
  } finally {
    await transport.close();
  }
});

test("actual React SSR renders all locale options with canonical alias and no resource/cookie work", () => {
  const Root = ({ children, ...props }) => {
    assert.equal(props.value, "nb");
    assert.equal(props.disabled, false);
    return React.createElement("div", null, children);
  };
  const controls = {
    Root,
    Trigger: ({ children }) => React.createElement("button", null, children),
    Value: ({ children }) => React.createElement("span", null, children),
    Content: ({ children }) => React.createElement("div", null, children),
    Item: ({ children, value, textValue, ...props }) =>
      React.createElement("span", { ...props, "data-value": value }, children),
  };
  const LocaleSelect = createLanguageSelector({
    ...jsx,
    useMemoCache,
    useState: React.useState,
    useTransition: React.useTransition,
    useTranslation: () => ({ i18n: { language: "NO-no" } }),
    useRouter: () => ({
      refresh() {
        throw Error("SSR refresh");
      },
    }),
    select: controls,
    catalog,
    changeLanguage() {
      throw Error("SSR language change");
    },
  });
  const html = renderToString(React.createElement(LocaleSelect));
  assert.equal((html.match(/data-testid="language-option-/g) ?? []).length, 35);
  assert.match(html, /Norsk/);
  assert.match(html, /Français/);
});
