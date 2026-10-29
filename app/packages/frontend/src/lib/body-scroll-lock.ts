type BodyLock = {
  count: number;
  priority: string;
  axes: { property: string; value: string; priority: string }[];
};
const locks = new WeakMap<HTMLElement, BodyLock>();

/** Keep each body locked until all of its owners release, preserving inline CSS. */
export function lockBodyScroll(): () => void {
  const body = document.body;
  let lock = locks.get(body);
  if (!lock) {
    lock = {
      count: 0,
      priority: body.style.getPropertyPriority("overflow"),
      axes: ["overflow-x", "overflow-y"].map((property) => ({
        property,
        value: body.style.getPropertyValue(property),
        priority: body.style.getPropertyPriority(property),
      })),
    };
    locks.set(body, lock);
  }
  lock.count += 1;
  body.style.setProperty("overflow", "hidden", lock.priority);
  let released = false;
  return () => {
    if (released) return;
    released = true;
    lock.count -= 1;
    if (lock.count === 0) {
      for (const { property, value, priority } of lock.axes) {
        body.style.setProperty(property, value, priority);
      }
      locks.delete(body);
    }
  };
}
