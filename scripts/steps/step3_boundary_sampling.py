#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Step 3: Sample nodes along obstacle boundaries.

This step:
1. Finds contours of inflated obstacles
2. Samples nodes along the contours at regular intervals
3. Connects sampled nodes along each contour
4. Adds boundary nodes to the existing graph
"""

import sys
from pathlib import Path

import cv2
import networkx as nx
import numpy as np

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


def find_obstacle_contours(dist_transform: np.ndarray, boundary_inflation: float):
    """Find contours of inflated obstacles.

    Args:
        dist_transform: Distance transform of free space
        boundary_inflation: Inflation distance in pixels

    Returns:
        List of contours
    """
    filtered_obstacles = (dist_transform >= boundary_inflation).astype(np.uint8)
    contours, _ = cv2.findContours(filtered_obstacles, cv2.RETR_LIST, cv2.CHAIN_APPROX_TC89_KCOS)
    return contours


def connect_contour_nodes(contour_nodes: list, graph: nx.Graph, inflated_map: np.ndarray):
    """Connect consecutive nodes along a contour.

    Args:
        contour_nodes: List of node coordinates along contour
        graph: NetworkX graph to add edges to
        inflated_map: Binary obstacle map for collision checking
    """
    for i in range(len(contour_nodes)):
        n1 = contour_nodes[i]
        n2 = contour_nodes[(i + 1) % len(contour_nodes)]

        if not check_line_collision(n1, n2, inflated_map):
            dist = np.sqrt((n1[0] - n2[0]) ** 2 + (n1[1] - n2[1]) ** 2)
            graph.add_edge(n1, n2, weight=dist, edge_type="contour")


def sample_obstacle_boundaries(
    graph: nx.Graph,
    dist_transform: np.ndarray,
    inflated_map: np.ndarray,
    boundary_inflation_px: float,
    sample_distance_px: int,
    logger
) -> int:
    """Sample nodes along obstacle boundaries.

    Args:
        graph: Existing graph to add boundary nodes to
        dist_transform: Distance transform
        inflated_map: Binary inflated obstacle map
        boundary_inflation_px: Boundary inflation in pixels
        sample_distance_px: Distance between samples in pixels
        logger: Logger instance

    Returns:
        Number of nodes added
    """
    logger.info(f"Finding obstacle contours (inflation: {boundary_inflation_px:.1f}px)...")
    contours = find_obstacle_contours(dist_transform, boundary_inflation_px)
    logger.info(f"Found {len(contours)} contours")

    initial_num_nodes = len(graph.nodes())

    for contour_idx, contour in enumerate(contours):
        contour_nodes = []

        # Process each vertex in the contour
        for i in range(len(contour)):
            p1 = contour[i][0]
            p2 = contour[(i + 1) % len(contour)][0]

            # Add first vertex
            row_1, col_1 = int(p1[1]), int(p1[0])
            contour_nodes.append((row_1, col_1))
            graph.add_node((row_1, col_1), node_type="boundary")

            # Calculate distance to next vertex
            segment_length = np.linalg.norm(p2 - p1)

            # Add intermediate points
            num_intermediate = int(segment_length / sample_distance_px)
            intermediate_points = np.linspace(p1, p2, num=num_intermediate, endpoint=False).astype(int).tolist()[1:]

            for point in intermediate_points:
                col, row = point
                contour_nodes.append((row, col))
                graph.add_node((row, col), node_type="boundary")

        # Connect nodes along this contour
        connect_contour_nodes(contour_nodes, graph, inflated_map)

    num_nodes_added = len(graph.nodes()) - initial_num_nodes
    logger.info(f"Added {num_nodes_added} boundary nodes")
    return num_nodes_added


def main():
    parser = create_step_parser(
        description="Step 3: Sample obstacle boundaries",
        requires_map=False
    )
    parser.add_argument(
        "--boundary-inflation-factor",
        type=float,
        default=1.5,
        help="Factor to inflate boundaries by safety distance"
    )
    parser.add_argument(
        "--boundary-sample-distance",
        type=float,
        default=2.5,
        help="Distance between samples along contour (meters)"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Save visualization of the graph"
    )
    args = parser.parse_args()

    logger = get_logger(__name__, args.log_level)
    logger.info("=" * 60)
    logger.info("Step 3: Boundary Sampling")
    logger.info("=" * 60)

    # Load previous step data
    step_data = load_step_data(args.input, "step2")

    # Get graph (create new if doesn't exist)
    graph = step_data.graph if step_data.graph is not None else nx.Graph()
    initial_nodes = len(graph.nodes())
    logger.info(f"Starting with {initial_nodes} nodes from previous step")

    # Convert parameters to pixels
    boundary_inflation_px = args.boundary_inflation_factor * step_data.safety_distance / step_data.resolution
    sample_distance_px = int(args.boundary_sample_distance / step_data.resolution)

    logger.info(f"Boundary inflation: {args.boundary_inflation_factor} * {step_data.safety_distance}m = {boundary_inflation_px:.1f}px")
    logger.info(f"Sample distance: {args.boundary_sample_distance}m = {sample_distance_px}px")

    # Sample boundaries
    if step_data.dist_transform is not None:
        sample_obstacle_boundaries(
            graph,
            step_data.dist_transform,
            step_data.inflated_map,
            boundary_inflation_px,
            sample_distance_px,
            logger
        )
    else:
        logger.warning("No distance transform available - skipping boundary sampling")

    logger.info(f"Total graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")

    # Save graph
    step_data.graph = graph
    save_step_data(step_data, args.output, "step3")

    # Visualize if requested
    if args.visualize and len(graph.nodes) > 0:
        output_path = f"{args.output}/step3_boundary_sampling.png"
        visualize_graph(graph, step_data.original_map, output_path)

    logger.info("Step 3 complete!")


if __name__ == "__main__":
    main()
