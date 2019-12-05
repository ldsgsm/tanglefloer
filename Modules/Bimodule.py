from __future__ import annotations
from networkx import MultiDiGraph
from typing import Iterable, Any
from pygraphviz import AGraph
from Modules import ETangleStrands
from SignAlgebra.AMinus import AMinus
from Modules.CTMinus import *


# Base class for Type DD, AA, DA, and AD structures
class Bimodule:
    def __init__(self, left_algebra: AMinus, right_algebra: AMinus,
                 generators: Iterable, maps: Iterable[Bimodule.Edge]):
        self.left_algebra = left_algebra
        self.right_algebra = right_algebra

        self.graph = MultiDiGraph()
        for gen in generators:
            self.graph.add_node(gen)
        for edge in maps:
            if edge.c != edge.target.etangle.polyring.zero():
                self.graph.add_edge(edge.source, edge.target,
                                    c=edge.c, left=edge.left, right=edge.right)

    def __repr__(self) -> str:
        return str(self.__dict__)

    def to_agraph(self, idempotents=True):
        out = AGraph(dpi=300)
        for node in self.graph.nodes:
            out.add_node(node,
                         label=str(dict(node.left_strands)) + str(dict(node.right_strands)),
                         shape='box',
                         fontname='Arial')
        for source in self.graph:
            for target in self.graph[source]:
                if not idempotents and target == source:
                    continue
                for i in self.graph[source][target]:
                    edge = self.graph[source][target][i]
                    color = 'black' if edge['right'] == tuple() else 'blue'
                    out.add_edge(source, target,
                                 label=str((edge['left'], edge['c'], edge['right'])),
                                 dir='forward',
                                 color=color,
                                 fontname='Arial')
        out.layout('dot')
        return out

    class Element:
        # d - {StrandDiagram: Z2Polynomial}
        def __init__(self, d=None):
            if d is None:
                d = {}
            self.d = {}
            for sd, c in d.items():
                if c != sd.etangle.polyring.zero():
                    self.d[sd] = c

        def __add__(self, other: Bimodule.Element) -> Bimodule.Element:
            out_d = dict(self.d)
            for sd in other.d:
                if sd in self.d:
                    out_d[sd] = self.d[sd] + other.d[sd]
                else:
                    out_d[sd] = other.d[sd]
            return Bimodule.Element(out_d)

        def __rmul__(self, other: Z2Polynomial):
            d_out = dict(self.d)
            for k in d_out:
                d_out[k] = other * d_out[k]
            return Bimodule.Element(d_out)

        def __eq__(self, other: Bimodule.Element) -> bool:
            return self.d == other.d

        def __repr__(self) -> str:
            return str(self.d)

    class Edge:
        def __init__(self, source, target, c: Z2Polynomial, left: Tuple, right: Tuple):
            self.source = source
            self.target = target
            self.c = c
            self.left = left
            self.right = right

        def __repr__(self) -> str:
            return str(self.__dict__)

        def __eq__(self, other: Bimodule.Edge) -> bool:
            return self.source == other.source and \
                   self.target == other.target and \
                   self.c == other.c and \
                   self.left == other.left and \
                   self.right == other.right


class TypeDA(Bimodule):
    def __init__(self, left_algebra: AMinus, right_algebra: AMinus,
                 generators: Iterable, maps: Iterable[Bimodule.Edge]):
        super().__init__(left_algebra, right_algebra, generators, maps)

    # TODO: this won't work because of polynomial ring mismatch
    def tensor(self, other: TypeDA) -> TypeDA:
        assert self.right_algebra == other.left_algebra

        generators = [(xm, xn)
                      for xm in self.graph.nodes for xn in other.graph.nodes]

        # something something idempotents match

        maps = []
        for (xm, xn) in generators:
            for ym in self.graph[xm]:
                for i in self.graph[xm][ym]:
                    delta_1 = self.graph[xm][ym][i]
                    if len(delta_1['left']) > 1:
                        continue
                    for yn in self.graph[xn]:
                        for j in self.graph[xn][yn]:
                            delta_n = self.graph[xn][yn][j]
                            if delta_1['right'] != delta_n['left']:
                                continue
                            maps.append(
                                Bimodule.Edge((xm, xn), (ym, yn),
                                              delta_1['c'] * delta_n['c'], delta_1['left'], delta_n['right']))

        return TypeDA(self.left_algebra, other.right_algebra, generators, maps)
