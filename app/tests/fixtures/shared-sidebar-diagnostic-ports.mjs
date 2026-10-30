// Authored diagnostic capabilities, not recovered Slot/CVA/Tooltip/Drawer/Next implementations.
export function diagnosticSidebarPorts(React, { jsx, jsxs, Fragment }) {
  const cn = (...values) => values.filter(Boolean).join(" "),
    DrawerContext = React.createContext(null);
  const plain = (tag) => (p) => jsx(tag, { ...p, children: p.children });
  const ports = {
    React,
    jsx,
    jsxs,
    Fragment,
    classNames: cn,
    classVariants:
      (base, config) =>
      (p = {}) =>
        cn(
          base,
          ...Object.entries(config.variants).map(
            ([key, values]) => values[p[key] ?? config.defaultVariants[key]],
          ),
        ),
    useTranslation: () => ({ t: (key) => key }),
    Slot({ children, ...props }) {
      return React.cloneElement(children, {
        ...props,
        className: cn(props.className, children.props.className),
      });
    },
    TooltipRoot: ({ children }) => jsx(Fragment, { children }),
    TooltipTrigger: ({ render }) => render,
    TooltipContent: ({ hidden, side, children }) =>
      jsx("span", {
        "data-diagnostic-tooltip": true,
        "data-side": side,
        hidden,
        children,
      }),
    DrawerRoot(p) {
      return jsx(DrawerContext.Provider, {
        value: p,
        children: jsx("div", {
          "data-diagnostic-drawer-root": true,
          hidden: !p.open,
          children: p.children,
        }),
      });
    },
    DrawerContent({ children, side, overlayClassName, ...props }) {
      const drawer = React.useContext(DrawerContext);
      return jsxs("div", {
        ...props,
        role: "dialog",
        "aria-label": "Synthetic mobile navigation",
        "data-diagnostic-side": side,
        children: [
          children,
          jsx("button", {
            "data-diagnostic-drawer-close": true,
            onClick: () => drawer.onOpenChange(false),
            children: "Synthetic drawer close",
          }),
        ],
      });
    },
    DrawerHeader: plain("header"),
    DrawerTitle: plain("h2"),
    DrawerDescription: plain("p"),
    makeSvgIcon: (spec) => (props) => {
      const render = (node, index) =>
        jsx(
          node.tag,
          { ...node.attr, children: node.child?.map(render) },
          index,
        );
      return jsx(spec.tag, {
        ...spec.attr,
        ...props,
        children: spec.child?.map(render),
      });
    },
    NewBadge: () =>
      jsx("span", {
        "data-diagnostic-new": true,
        children: "Synthetic new badge",
      }),
    ExternalIcon: () =>
      jsx("span", {
        "data-diagnostic-external": true,
        "aria-hidden": true,
        children: "↗",
      }),
  };
  return ports;
}
