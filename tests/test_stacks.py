# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import pytest

from landoui.stacks import (
    draw_stack_graph,
    Edge,
    sort_stack_topological,
)


def test_sort_stack_topological_single_node():
    order = sort_stack_topological({"PHID-DREV-0"}, set())
    assert len(order) == 1
    assert order[0] == "PHID-DREV-0"


def test_sort_stack_topological_linear():
    revs = ["PHID-DREV-{}".format(i) for i in range(10)]
    nodes = {phid for phid in revs}
    edges = {Edge(child=revs[i], parent=revs[i - 1]) for i in range(1, 10)}

    order = sort_stack_topological(nodes, edges)
    assert order == revs


def test_sort_stack_topological_favors_minimum():
    nodes = set(range(10))
    edges = {Edge(child=0, parent=i) for i in range(1, 10)}

    order = sort_stack_topological(nodes, edges)
    assert order == list(range(1, 10)) + [0]


def test_sort_stack_topological_cycle():
    nodes = {1, 2, 3, 4}
    edges = {
        Edge(child=1, parent=2),
        Edge(child=2, parent=3),
        Edge(child=3, parent=1),
        Edge(child=1, parent=4),
    }

    with pytest.raises(ValueError):
        sort_stack_topological(nodes, edges)


def test_sort_stack_topological_complex():
    nodes = set('PHID-DREV-{}'.format(i) for i in range(10))
    edges = {
        Edge(child='PHID-DREV-1', parent='PHID-DREV-0'),
        Edge(child='PHID-DREV-2', parent='PHID-DREV-0'),
        Edge(child='PHID-DREV-2', parent='PHID-DREV-3'),
        Edge(child='PHID-DREV-4', parent='PHID-DREV-2'),
        Edge(child='PHID-DREV-5', parent='PHID-DREV-4'),
        Edge(child='PHID-DREV-6', parent='PHID-DREV-1'),
        Edge(child='PHID-DREV-7', parent='PHID-DREV-6'),
        Edge(child='PHID-DREV-7', parent='PHID-DREV-5'),
        Edge(child='PHID-DREV-9', parent='PHID-DREV-7'),
        Edge(child='PHID-DREV-8', parent='PHID-DREV-9'),
    }

    order = sort_stack_topological(
        nodes, edges, key=lambda x: int(x.split('-')[2])
    )
    assert order == [
        'PHID-DREV-0',
        'PHID-DREV-1',
        'PHID-DREV-3',
        'PHID-DREV-2',
        'PHID-DREV-4',
        'PHID-DREV-5',
        'PHID-DREV-6',
        'PHID-DREV-7',
        'PHID-DREV-9',
        'PHID-DREV-8',
    ]


def test_draw_stack_graph_complex():
    nodes = set('PHID-DREV-{}'.format(i) for i in range(10))
    edges = {
        Edge(child='PHID-DREV-1', parent='PHID-DREV-0'),
        Edge(child='PHID-DREV-2', parent='PHID-DREV-0'),
        Edge(child='PHID-DREV-2', parent='PHID-DREV-3'),
        Edge(child='PHID-DREV-4', parent='PHID-DREV-2'),
        Edge(child='PHID-DREV-5', parent='PHID-DREV-4'),
        Edge(child='PHID-DREV-6', parent='PHID-DREV-1'),
        Edge(child='PHID-DREV-7', parent='PHID-DREV-6'),
        Edge(child='PHID-DREV-7', parent='PHID-DREV-5'),
        Edge(child='PHID-DREV-9', parent='PHID-DREV-7'),
        Edge(child='PHID-DREV-8', parent='PHID-DREV-9'),
    }
    order = sort_stack_topological(
        nodes, edges, key=lambda x: int(x.split('-')[2])
    )

    width, rows = draw_stack_graph(nodes, edges, order)
    assert width == 3
    assert rows == [
        {
            'above': [0, 1],
            'below': [],
            'node': 'PHID-DREV-0',
            'other': [],
            'pos': 0
        }, {
            'above': [0],
            'below': [0],
            'node': 'PHID-DREV-1',
            'other': [1],
            'pos': 0
        }, {
            'above': [2],
            'below': [],
            'node': 'PHID-DREV-3',
            'other': [0, 1],
            'pos': 2
        }, {
            'above': [1],
            'below': [1, 2],
            'node': 'PHID-DREV-2',
            'other': [0],
            'pos': 1
        }, {
            'above': [1],
            'below': [1],
            'node': 'PHID-DREV-4',
            'other': [0],
            'pos': 1
        }, {
            'above': [1],
            'below': [1],
            'node': 'PHID-DREV-5',
            'other': [0],
            'pos': 1
        }, {
            'above': [0],
            'below': [0],
            'node': 'PHID-DREV-6',
            'other': [1],
            'pos': 0
        }, {
            'above': [0],
            'below': [0, 1],
            'node': 'PHID-DREV-7',
            'other': [],
            'pos': 0
        }, {
            'above': [0],
            'below': [0],
            'node': 'PHID-DREV-9',
            'other': [],
            'pos': 0
        }, {
            'above': [],
            'below': [0],
            'node': 'PHID-DREV-8',
            'other': [],
            'pos': 0
        }
    ]
