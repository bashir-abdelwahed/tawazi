"""Module containing the definition of a Directed Graph Extension of networkx.DiGraph."""
from itertools import chain
from typing import Dict, Iterable, List, Sequence, Set

import networkx as nx
from networkx import NetworkXNoCycle, NetworkXUnfeasible, find_cycle

from tawazi.consts import Identifier, Tag
from tawazi.errors import TawaziUsageError
from tawazi.node import ExecNode, UsageExecNode


class DiGraphEx(nx.DiGraph):
    """Extends the DiGraph with some methods."""

    @classmethod
    def from_exec_nodes(
        cls, exec_nodes: Dict[Identifier, ExecNode], input_nodes: List[UsageExecNode]
    ) -> "DiGraphEx":
        """Build a DigraphEx from exec nodes.

        Args:
            input_nodes: nodes that are the inputs of the graph
            exec_nodes: the graph nodes

        Returns:
            the DigraphEx object
        """
        graph = DiGraphEx()

        input_ids = [uxn.id for uxn in input_nodes]
        for node in exec_nodes.values():
            # add node and edges
            graph.add_node(node.id)
            graph.add_edges_from([(dep.id, node.id) for dep in node.dependencies])

            # add tag, setup and debug
            if node.tag:
                if isinstance(node.tag, Tag):
                    graph.nodes[node.id]["tag"] = [node.tag]
                else:
                    graph.nodes[node.id]["tag"] = [t for t in node.tag]

            graph.nodes[node.id]["debug"] = node.debug
            graph.nodes[node.id]["setup"] = node.setup

            # validate setup ExecNodes
            if node.setup and any(dep.id in input_ids for dep in node.dependencies):
                raise TawaziUsageError(
                    f"The ExecNode {node} takes as parameters one of the DAG's input parameter"
                )

        # check for circular dependencies
        try:
            cycle = find_cycle(graph)
            raise NetworkXUnfeasible(f"the DAG contains at least a circular dependency: {cycle}")
        except NetworkXNoCycle:
            pass

        return graph

    @property
    def root_nodes(self) -> List[Identifier]:
        """Safely gets the root nodes.

        Returns:
            List of root nodes
        """
        return [node for node, degree in self.in_degree if degree == 0]

    @property
    def leaf_nodes(self) -> List[Identifier]:
        """Safely get the leaf nodes.

        Returns:
            List of leaf nodes
        """
        return [node for node, degree in self.out_degree if degree == 0]

    @property
    def debug_nodes(self) -> List[Identifier]:
        """Get the debug nodes.

        Returns:
            the debug nodes
        """
        return [node for node, debug in self.nodes(data="debug") if debug]

    @property
    def setup_nodes(self) -> List[Identifier]:
        """Get the setup nodes.

        Returns:
            the setup nodes
        """
        return [node for node, setup in self.nodes(data="setup") if setup]

    @property
    def tags(self) -> Set[str]:
        """Get all the tags available for the graph.

        Returns:
            A set of tags
        """
        return set(chain([tags for _, tags in self.nodes(data="tag")]))

    def get_tagged_nodes(self, tag: Tag) -> List[str]:
        """Get nodes with a certain tag.

        Args:
            tag: the tag identifier

        Returns:
            a list of nodes
        """
        return [xn for xn, tags in self.nodes(data="tag") if tags is not None and tag in tags]

    def single_node_successors(self, node_id: Identifier) -> List[Identifier]:
        """Get all the successors of a node with a depth first search.

        Args:
            node_id: the node acting as the root of the search

        Returns:
            list of the node's successors
        """
        return list(nx.dfs_tree(self, node_id).nodes())

    def multiple_nodes_successors(self, nodes_ids: Sequence[Identifier]) -> Set[Identifier]:
        """Get the successors of all nodes in the iterable.

        Args:
            nodes_ids: nodes of which we want successors

        Returns:
            a set of all the sucessors
        """
        return set(list(chain(*[self.single_node_successors(node) for node in nodes_ids])))

    def remove_recursively(self, root_node: Identifier, remove_root_node: bool = True) -> None:
        """Recursively removes all the nodes that depend on the provided.

        Args:
            root_node (Identifier): the root node
            remove_root_node (bool, optional): whether to remove the root node or not. Defaults to True.
        """
        nodes_to_remove = self.single_node_successors(root_node)

        # skip removing the root node if requested
        if not remove_root_node:
            nodes_to_remove.remove(root_node)

        for node in nodes_to_remove:
            self.remove_node(node)

    def get_runnable_debug_nodes(self, leaves_ids: List[Identifier]) -> List[Identifier]:
        """Get debug nodes that are runnable with provided nodes as direct roots.

        For example:
        A
        |
        B
        | \
        D E

        if D is not a debug ExecNode and E is a debug ExecNode.
        If the subgraph whose leaf ExecNode D is executed,
        E should also be included in the execution because it can be executed (debug node whose inputs are provided)
        Hence we should extend the subgraph containing only D to also contain E

        Args:
            leaves_ids: the leaves ids of the subgraph

        Returns:
            the leaves ids of the new extended subgraph that contains more debug ExecNodes
        """
        new_debug_xn_discovered = True
        while new_debug_xn_discovered:
            new_debug_xn_discovered = False
            for id_ in leaves_ids:
                for successor_id in self.successors(id_):
                    if successor_id not in leaves_ids and successor_id in self.debug_nodes:
                        # a new debug XN has been discovered!
                        if set(self.predecessors(successor_id)).issubset(set(leaves_ids)):
                            new_debug_xn_discovered = True
                            # this new XN can run by only running the current leaves_ids
                            leaves_ids.append(successor_id)
        return leaves_ids

    def minimal_induced_subgraph(self, nodes: List[Identifier]) -> "DiGraphEx":
        """Get the minimal induced subgraph containing the provided nodes.

        The generated subgraph contains the provided nodes as leaf nodes.
        For example:
        graph =
        "
        A
        | \
        B  C
        |  |\
        D  E F
        "
        subgraph_leaves(D, C, E) ->
        "
        A
        | \
        B  C
        |  |
        D  E
        "
        C is not a node that can be made into leaf nodes

        Args:
            nodes: the list of nodes to be executed

        Returns:
            the induced subgraph over the original graph with the provided nodes:

        Raises:
            ValueError: if the provided nodes are not in the graph
        """
        if any([node not in self.nodes for node in nodes]):
            raise ValueError(
                f"The provided nodes are not in the graph. "
                f"The provided nodes are: {nodes}."
                f"The graph only contains: {self.nodes}."
            )

        # compute all the ancestor nodes that will be included in the graph
        all_ancestors = self.ancestors_of_iter(nodes)
        induced_subgraph: DiGraphEx = nx.induced_subgraph(self, all_ancestors | set(nodes))
        return induced_subgraph

    @property
    def topologically_sorted(self) -> List[Identifier]:
        """Makes the simple topological sort of the graph nodes.

        Returns:
            List of nodes of the graph listed in topological order
        """
        return list(nx.topological_sort(self))

    def ancestors_of_iter(self, nodes: Iterable[Identifier]) -> Set[Identifier]:
        """Returns the ancestors of the provided nodes.

        Args:
            nodes (Set[Identifier]): The nodes to find the ancestors of

        Returns:
            Set[Identifier]: The ancestors of the provided nodes
        """
        return set().union(*chain(nx.ancestors(G=self, source=node) for node in nodes))
