#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Step 6: Prune and optimize the graph.

This step:
1. Merges nodes that are too close together
2. Removes isolated nodes with no connections
3. Removes small disconnected subgraphs
4. Converts to world coordinates
5. Saves final graph
"""

import sys
from pathlib import Path

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.steps.common import (
    create_step_parser,
    get_logger,
    load_step_data,
    save_graph,
    visualize_graph,
)
from swagger.models import Point
from swagger.utils import pixel_to_world


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


def merge_close_nodes(
    graph: nx.Graph,
    inflated_map: np.ndarray,
    threshold_px: int,
    logger
) -> int:
    """Merge nodes that are within threshold distance.

    Args:
        graph: NetworkX graph
        inflated_map: Binary obstacle map for collision checking
        threshold_px: Distance threshold in pixels
        logger: Logger instance

    Returns:
        Number of nodes removed
    """
    initial_num_nodes = len(graph.nodes())
    iteration = 0

    while True:
        iteration += 1
        nodes = list(graph.nodes())
        if len(nodes) == 0:
            break

        node_coords = np.array(nodes)
        tree = cKDTree(node_coords)

        # Find pairs of nodes that are close
        pairs = tree.query_pairs(r=threshold_px)

        if not pairs:
            break

        merged = False

        for n1_idx, n2_idx in pairs:
            n1 = nodes[n1_idx]
            n2 = nodes[n2_idx]

            # Skip if n2 already removed
            if not graph.has_node(n2):
                continue

            # Check if all n2's neighbors can connect to n1
            neighbors = [n for n in graph.neighbors(n2) if n != n1]

            if neighbors:
                collision = False
                for dst in neighbors:
                    if check_line_collision(n1, dst, inflated_map):
                        collision = True
                        break

                # Only merge if all connections are valid
                if not collision:
                    for neighbor in neighbors:
                        dist = np.sqrt((neighbor[0] - n1[0]) ** 2 + (neighbor[1] - n1[1]) ** 2)
                        graph.add_edge(n1, neighbor, weight=dist, edge_type="merge")
                    graph.remove_node(n2)
                    merged = True
            else:
                # No neighbors, safe to remove
                graph.remove_node(n2)
                merged = True

        if not merged:
            break

        logger.debug(f"Merge iteration {iteration}: {initial_num_nodes - len(graph.nodes())} nodes removed so far")

    num_removed = initial_num_nodes - len(graph.nodes())
    logger.info(f"Merged {num_removed} close nodes in {iteration} iterations")
    return num_removed


def remove_small_subgraphs(
    graph: nx.Graph,
    min_subgraph_length_px: int,
    logger
) -> int:
    """Remove disconnected subgraphs that are too small.

    Args:
        graph: NetworkX graph
        min_subgraph_length_px: Minimum total edge length in pixels
        logger: Logger instance

    Returns:
        Number of nodes removed
    """
    initial_num_nodes = len(graph.nodes())

    # Find connected components
    components = list(nx.connected_components(graph))
    logger.info(f"Found {len(components)} connected components")

    for component in components:
        subgraph = graph.subgraph(component)
        total_length = sum(d["weight"] for _, _, d in subgraph.edges(data=True))

        if total_length < min_subgraph_length_px:
            logger.debug(f"Removing small subgraph: {len(component)} nodes, {total_length:.1f}px total length")
            graph.remove_nodes_from(component)

    num_removed = initial_num_nodes - len(graph.nodes())
    logger.info(f"Removed {num_removed} nodes from small subgraphs")
    return num_removed


def to_world_coordinates(
    graph: nx.Graph,
    resolution: float,
    x_offset: float,
    y_offset_adjusted: float,
    cos_rot: float,
    sin_rot: float,
    logger
) -> nx.Graph:
    """Convert graph from pixel to world coordinates.

    Args:
        graph: Graph in pixel coordinates
        resolution: Meters per pixel
        x_offset: X offset in meters
        y_offset_adjusted: Adjusted Y offset in meters
        cos_rot: Cosine of rotation angle
        sin_rot: Sine of rotation angle
        logger: Logger instance

    Returns:
        New graph with world coordinates
    """
    logger.info("Converting to world coordinates...")

    world_graph = nx.Graph()
    pixel_to_id_lookup = {}

    # Convert nodes
    for i, (node, data) in enumerate(graph.nodes(data=True)):
        row, col = node
        world_point = pixel_to_world(row, col, resolution, x_offset, y_offset_adjusted, cos_rot, sin_rot)
        world_point_array = (world_point.x, world_point.y, world_point.z)
        pixel = (int(row), int(col))
        world_graph.add_node(i, world=world_point_array, pixel=pixel, **data)
        pixel_to_id_lookup[node] = i

    # Convert edges (scale weights by resolution)
    for src, dst, data in graph.edges(data=True):
        data["weight"] = float(data["weight"]) * resolution
        world_graph.add_edge(pixel_to_id_lookup[src], pixel_to_id_lookup[dst], **data)

    logger.info(f"Converted graph: {len(world_graph.nodes)} nodes, {len(world_graph.edges)} edges")
    return world_graph


def main():
    parser = create_step_parser(
        description="Step 6: Prune and finalize graph",
        requires_map=False
    )
    parser.add_argument(
        "--merge-node-distance",
        type=float,
        default=0.25,
        help="Maximum distance to merge nodes (meters)"
    )
    parser.add_argument(
        "--min-subgraph-length",
        type=float,
        default=0.25,
        help="Minimum total edge length to keep subgraph (meters)"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Save visualization of the graph"
    )
    parser.add_argument(
        "--output-graph",
        type=str,
        default="final_graph.pkl",
        help="Output filename for final graph"
    )
    args = parser.parse_args()

    logger = get_logger(__name__, args.log_level)
    logger.info("=" * 60)
    logger.info("Step 6: Graph Pruning and Finalization")
    logger.info("=" * 60)

    # Load previous step data
    step_data = load_step_data(args.input, "step5")

    # Get graph
    if step_data.graph is None or len(step_data.graph.nodes()) == 0:
        logger.warning("No graph available - creating empty graph")
        graph = nx.Graph()
    else:
        graph = step_data.graph
        logger.info(f"Starting with {len(graph.nodes)} nodes, {len(graph.edges)} edges")

        # Convert parameters to pixels
        merge_distance_px = int(args.merge_node_distance / step_data.resolution)
        min_length_px = int(args.min_subgraph_length / step_data.resolution)

        logger.info(f"Merge distance: {args.merge_node_distance}m = {merge_distance_px}px")
        logger.info(f"Min subgraph length: {args.min_subgraph_length}m = {min_length_px}px")

        # Merge close nodes
        if len(graph.nodes()) > 0:
            merge_close_nodes(graph, step_data.inflated_map, merge_distance_px, logger)

        # Remove isolated nodes
        isolated = list(nx.isolates(graph))
        if isolated:
            graph.remove_nodes_from(isolated)
            logger.info(f"Removed {len(isolated)} isolated nodes")

        # Remove small subgraphs
        remove_small_subgraphs(graph, min_length_px, logger)

        logger.info(f"After pruning: {len(graph.nodes)} nodes, {len(graph.edges)} edges")

    # Convert to world coordinates
    if len(graph.nodes()) > 0:
        world_graph = to_world_coordinates(
            graph,
            step_data.resolution,
            step_data.x_offset,
            step_data.y_offset_adjusted,
            step_data.cos_rot,
            step_data.sin_rot,
            logger
        )
    else:
        world_graph = nx.Graph()

    # Save final graph
    save_graph(world_graph, args.output, args.output_graph)

    # Visualize if requested (use pixel coordinates from world graph)
    if args.visualize and len(world_graph.nodes) > 0:
        output_path = f"{args.output}/step6_final_graph.png"
        visualize_graph(world_graph, step_data.original_map, output_path)

    logger.info("=" * 60)
    logger.info("Graph generation complete!")
    logger.info(f"Final graph: {len(world_graph.nodes)} nodes, {len(world_graph.edges)} edges")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
