from collections.abc import Collection
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

from gplugins.klayout.netlist_graph import networkx_from_file


def plot_nets(
    filepath: str | Path,
    fully_connected: bool = False,
    interactive: bool = False,
    include_labels: bool = True,
    only_most_complex: bool = False,
    nodes_to_reduce: Collection[str] | None = None,
) -> None:
    """Plots the connectivity between the components in the KLayout LayoutToNetlist file from :func:`~get_l2n`.

    Args:
        filepath: Path to the KLayout LayoutToNetlist file or a SPICE netlist.
            File extensions should be `.l2n` and `.spice`, respectively.
        fully_connected: Whether to plot the graph as elements fully connected to all other ones (True) or
            going through other elements (False).
        interactive: Whether to plot an interactive graph with `pyvis` or not.
        include_labels: Whether to include labels in the graph connected to corresponding cells.
        only_most_complex: Whether to plot only the circuit with most connections or not.
            Helpful for not plotting subcircuits separately.
        nodes_to_reduce: Nodes to reduce to a single edge. Comparison made with Python ``in`` operator.
            Helpful for reducing trivial waveguide elements.
    """

    G_connectivity = networkx_from_file(**locals())

    if nodes_to_reduce:

        def _removal_condition(node: str, degree: int) -> bool:
            return degree == 2 and any(e in node for e in nodes_to_reduce)

        while any(
            _removal_condition(node, degree) for node, degree in G_connectivity.degree
        ):
            G_connectivity_tmp = G_connectivity.copy()
            for node, degree in G_connectivity.degree:
                if _removal_condition(node, degree):
                    connected_to_node = [e[1] for e in G_connectivity.edges(node)]
                    node_pairs_to_connect = list(combinations(connected_to_node, r=2))
                    for pair in node_pairs_to_connect:
                        G_connectivity_tmp.add_edge(pair[0], pair[1])
                    G_connectivity_tmp.remove_node(node)
                    break
            G_connectivity = G_connectivity_tmp

    # Plotting the graph
    if interactive:
        try:
            from pyvis.network import Network
        except ModuleNotFoundError as e:
            raise UserWarning(
                "You need to `pip install pyvis<=0.3.1` or `gplugins[klayout]`"
            ) from e

        net = Network(
            select_menu=True,
            filter_menu=True,
        )
        net.show_buttons()
        net.from_nx(G_connectivity)
        net.show("connectivity.html")
    else:
        plt.figure(figsize=(8, 6))
        nx.draw(
            G_connectivity,
            with_labels=True,
            node_size=2000,
            node_color="lightpink",
            font_size=12,
        )
        plt.title("Connectivity")
        plt.show()


if __name__ == "__main__":
    from gdsfactory.samples.demo.lvs import pads_correct, pads_shorted

    from gplugins.common.config import PATH
    from gplugins.klayout.get_netlist import get_l2n

    c = pads_correct()
    c = pads_shorted()
    c.show()

    gdspath = c.write_gds(PATH.extra / "pads.gds")

    l2n = get_l2n(gdspath)
    path = PATH.extra / f"{c.name}.txt"
    l2n.write_l2n(str(path))

    plot_nets(path)
