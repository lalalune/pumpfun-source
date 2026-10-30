"""Iterative SCC analysis of internal CFG edges; not dynamic loop inference."""


def cycle_regions(blocks):
    graph = {b['offset']: sorted({e['target'] for e in b['successors'] if e['internal']}) for b in blocks}
    reverse = {node: [] for node in graph}
    for source, targets in graph.items():
        for target in targets:
            reverse[target].append(source)
    seen, finished = set(), []
    for root in graph:
        if root in seen:
            continue
        seen.add(root)
        pending = [(root, iter(graph[root]))]
        while pending:
            node, children = pending[-1]
            child = next(children, None)
            if child is None:
                finished.append(node)
                pending.pop()
            elif child not in seen:
                seen.add(child)
                pending.append((child, iter(graph[child])))
    assigned, regions = set(), []
    reachable = {b['offset'] for b in blocks if b['reachable']}
    for root in reversed(finished):
        if root in assigned:
            continue
        component, pending = set(), [root]
        assigned.add(root)
        while pending:
            node = pending.pop()
            component.add(node)
            for parent in reverse[node]:
                if parent not in assigned:
                    assigned.add(parent)
                    pending.append(parent)
        if len(component) > 1 or root in graph[root]:
            regions.append({'blocks': sorted(component), 'reachable': bool(component & reachable),
                            'entry_blocks': sorted(node for node in component
                                                   if node == 0 or any(p not in component for p in reverse[node]))})
    return sorted(regions, key=lambda row: row['blocks'][0])
