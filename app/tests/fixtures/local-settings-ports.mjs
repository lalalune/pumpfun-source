// Synthetic capabilities only: no global browser storage or cookie access.
export class SyntheticStorageEvent extends Event {
  constructor(type, init = {}) {
    super(type);
    this.key = init.key;
  }
}
export function syntheticSettingsWindow(initial = {}) {
  const values = new Map(Object.entries(initial));
  const events = new EventTarget();
  const calls = [];
  const failures = {
    read: false,
    write: false,
    remove: false,
    dispatch: false,
  };
  const localStorage = {
    getItem(key) {
      calls.push(["read", key]);
      if (failures.read) throw Error("synthetic read denied");
      return values.get(key) ?? null;
    },
    setItem(key, value) {
      calls.push(["write", key, value]);
      if (failures.write) throw Error("synthetic write denied");
      values.set(key, String(value));
    },
    removeItem(key) {
      calls.push(["remove", key]);
      if (failures.remove) throw Error("synthetic remove denied");
      values.delete(key);
    },
  };
  const window = {
    localStorage,
    addEventListener(type, callback) {
      calls.push(["listen", type]);
      events.addEventListener(type, callback);
    },
    dispatchEvent(event) {
      calls.push(["dispatch", event.type, event.key]);
      if (failures.dispatch) throw Error("synthetic dispatch denied");
      return events.dispatchEvent(event);
    },
  };
  return { window, values, calls, failures };
}
