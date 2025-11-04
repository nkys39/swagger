#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Step 5: Add Delaunay triangulation shortcuts.

This step:
1. Computes Delaunay triangulation of all nodes
2. Checks each triangle edge for collisions
3. Adds collision-free edges as shortcuts
4. Improves path optimality by connecting nearby nodes
"""

import sys
from pathlib import Path

import networkx as nx
import numpy as np
from scipy.spatial import Delaunay

# Add steps directory to path
sys.path.insert(0, str(Path(__file__).parent))

from common import (
    create_step_parser,
    get_logger,
    load_step_data,
    save_step_data,
    visualize_graph,
)


def check_line_collision(p0, p1, inflated_map):
    """Check if line between two points intersects obstacles."""
    y0, x0 = p0
    y1, x1 = p1
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        if inflated_map[y0, x0]:
            return True
        if (y0 == y1) and (x0 == x1):
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

    return False


def add_delaunay_shortcuts(
    graph: nx.Graph,
    inflated_map: np.ndarray,
    logger
) -> int:
    """Add shortcuts based on Delaunay triangulation.

    Args:
        graph: Existing graph
        inflated_map: Binary obstacle map for collision checking
        logger: Logger instance

    Returns:
        Number of edges added
    """
    nodes = list(graph.nodes())
    if len(nodes) < 3:
        logger.warning("Need at least 3 nodes for Delaunay triangulation")
        return 0

    # Compute Delaunay triangulation
    logger.info(f"Computing Delaunay triangulation of {len(nodes)} nodes...")
    node_coords = np.array(nodes)

    try:
        tri = Delaunay(node_coords)
    except Exception as e:
        logger.error(f"Delaunay triangulation failed: {e}")
        return 0

    logger.info(f"Generated {len(tri.simplices)} triangles")

    # Collect candidate edges
    edge_candidates = set()
    for simplex in tri.simplices:
        for i in range(3):
            n1, n2 = tuple(sorted([nodes[simplex[i]], nodes[simplex[(i + 1) % 3]]]))
            if not graph.has_edge(n1, n2):
                edge_candidates.add((n1, n2))

    logger.info(f"Found {len(edge_candidates)} candidate edges")

    # Add valid edges
    initial_num_edges = len(graph.edges())
    for n1, n2 in edge_candidates:
        if not check_line_collision(n1, n2, inflated_map):
            dist = np.sqrt((n2[0] - n1[0]) ** 2 + (n2[1] - n1[1]) ** 2)
            graph.add_edge(n1, n2, weight=dist, edge_type="delaunay")

    num_edges_added = len(graph.edges()) - initial_num_edges
    logger.info(f"Added {num_edges_added} Delaunay shortcut edges")
    return num_edges_added


def main():
    parser = create_step_parser(
        description="Step 5: Add Delaunay shortcuts",
        requires_map=False
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Save visualization of the graph"
    )
    args = parser.parse_args()

    logger = get_logger(__name__, args.log_level)
    logger.info("=" * 60)
    logger.info("Step 5: Delaunay Shortcuts")
    logger.info("=" * 60)

    # Load previous step data (try step4, step3, step2, then step1)
    for step_name in ["step4", "step3", "step2", "step1"]:
        try:
            step_data = load_step_data(args.input, step_name)
            logger.info(f"Loaded data from {step_name}")
            break
        except FileNotFoundError:
            continue
    else:
        raise FileNotFoundError("No previous step data found (tried step4, step3, step2, step1)")

    # Get graph
    if step_data.graph is None or len(step_data.graph.nodes()) == 0:
        logger.warning("No graph available - skipping Delaunay shortcuts")
        graph = nx.Graph()
    else:
        graph = step_data.graph
        initial_edges = len(graph.edges())
        logger.info(f"Starting with {len(graph.nodes)} nodes, {initial_edges} edges")

        # Add shortcuts
        add_delaunay_shortcuts(graph, step_data.inflated_map, logger)

        logger.info(f"Total graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")

    # Save graph
    step_data.graph = graph
    save_step_data(step_data, args.output, "step5")

    # Visualize if requested
    if args.visualize and len(graph.nodes) > 0:
        output_path = f"{args.output}/step5_delaunay_shortcuts.png"
        visualize_graph(graph, step_data.original_map, output_path)

    logger.info("Step 5 complete!")


if __name__ == "__main__":
    main()
