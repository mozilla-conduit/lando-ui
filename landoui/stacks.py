# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from collections import namedtuple
from types import SimpleNamespace

Edge = namedtuple("Edge", ("child", "parent"))
Node = namedtuple("Node", ("id", "children", "parents"))


def graph(nodes, edges):
    """Construct a graph dictionary from nodes and edges.

    Args:
        nodes: A set() of node identifiers which form the stack. Each
            node identifier is most likely a string PHID, but isn't
            required to be.
        edges: A set() of Edge objects, identifying the edges between
            nodes in the stack. The "children" and "parents" fields of
            each edge should contain a set of node identifiers.

    Returns:
        A dictionary mapping node identifiers to Node objects.
    """
    g = {node: Node(id=node, children=set(), parents=set()) for node in nodes}

    for e in edges:
        g[e.parent].children.add(e.child)
        g[e.child].parents.add(e.parent)

    return g


def sort_stack_topological(nodes, edges, *, key=lambda x: x):
    """Return a topological sort of the stack revisions.

    Args:
        nodes: A set() of node identifiers which form the stack. Each
            node identifier is most likely a string PHID, but isn't
            required to be.
        edges: A set() of Edge objects, identifying the edges between
            nodes in the stack. The "children" and "parents" fields of
            each edge should contain a set of node identifiers.
        key: A callable which can be used to change the sort key
            when breaking ties in the topological sort. By default
            the identity function will be used causing the default
            sort behaviour. This parameter can be useful when the
            node identifiers are complex objects are some secondary
            preference to ordering should be applied.

    Returns:
        A topologically sorted list of node identifiers.

    Raises:
        ValueError: If the provided stack contains a cycle.
    """
    g = graph(nodes, edges)

    sources = {node for node in g if not g[node].parents}
    order = []

    while sources:
        node = min(sources, key=key)
        sources.remove(node)
        order.append(node)

        for child in g.pop(node).children:
            g[child].parents.remove(node)

            if not g[child].parents:
                sources.add(child)

    if g:
        raise ValueError('Provided graph has a cycle.')

    return order


def draw_stack_graph(nodes, edges, order):
    """Return metadata useful for representing a stack visually.

    Args:
        nodes: A set() of node identifiers which form the stack. Each
            node identifier is most likely a string PHID, but isn't
            required to be.
        edges: A set() of Edge objects, identifying the edges between
            nodes in the stack. The "children" and "parents" fields of
            each edge should contain a set of node identifiers.
        order: A list of node identifiers in topological sorted order.

    Returns:
        A tuple (width, rows). `width` is the number of columns
        wide the graph drawing should be. `rows` is a list of
        dictionaries, each representing the data needed to draw
        the graph for the corresponding node from order. Each
        row contains the following keys:
          - 'node': The node identifier for the row.
          - 'pos': The column this node should be placed in.
          - 'above': A list of columns the node should connect to above.
          - 'below': A list of columns the node should connect to below.
          - 'other': A list of columns which should connect vertically
                     from top to bottom.
    """
    g = graph(nodes, edges)
    next_node = []
    drawing = SimpleNamespace(rows=[], width=0)

    def empty_column_or_new():
        """Return the index of an empty column or create a new one."""
        if not next_node.count(None):
            next_node.append(None)
            drawing.width += 1
            return drawing.width - 1

        return next_node.index(None)

    # Iterate over the order and build the drawing.
    for i, node in enumerate(order):
        # What column should this node go in?
        col = (
            next_node.index(node)
            if next_node.count(node) else empty_column_or_new()
        )

        # Calculate connections from earlier rows.
        below = set()
        for from_col in range(len(next_node)):
            target = next_node[from_col]
            if target == node:
                below.add(from_col)

                # Because we've connected this column it should
                # now be free.
                next_node[from_col] = None

        # What columns need to connect vertically to continue?
        other = {i for i, target in enumerate(next_node) if target is not None}

        # Order the children for placement.
        above = set()
        if g[node].children:
            # Place the closest child in the order above
            # the current node.
            closest = order[min(
                [order.index(child) for child in g[node].children]
            )]
            next_node[col] = closest
            above.add(col)

            for child in g[node].children:
                if child != closest:
                    position = empty_column_or_new()
                    next_node[position] = child
                    above.add(position)

        drawing.rows.append(
            {
                'node': node,
                'pos': col,
                'above': sorted(above),
                'below': sorted(below),
                'other': sorted(other),
            }
        )

    return drawing.width, drawing.rows
