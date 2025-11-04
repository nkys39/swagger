#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Step 4: Sample nodes in free space areas.

This step:
1. Identifies large free space areas far from existing nodes
2. Finds local maxima in distance map
3. Adds nodes at strategic locations to improve coverage
4. Uses iterative sampling until no large gaps remain
"""

import sys
from pathlib import Path

import cv2
import networkx as nx
import numpy as np
from rtree import index

# Add steps directory to path
sys.path.insert(0, str(Path(__file__).parent))

from common import (
    create_step_parser,
    get_logger,
    load_step_data,
    save_step_data,
    visualize_graph,
)


def sample_free_space(
    graph: nx.Graph,
    original_map: np.ndarray,
    occupancy_threshold: int,
    distance_threshold_px: int,
    logger
) -> int:
    """Iteratively sample free space areas.

    Args:
        graph: Existing graph to add nodes to
        original_map: Original occupancy grid
        occupancy_threshold: Threshold for occupied cells
        distance_threshold_px: Threshold for identifying large gaps (pixels)
        logger: Logger instance

    Returns:
        Number of nodes added
    """
    initial_num_nodes = len(graph.nodes())

    # Initialize distance map
    distance_map = np.full(original_map.shape, np.inf, dtype=np.float64)

    # Set occupied pixels to 0
    distance_map[original_map <= occupancy_threshold] = 0

    # Set existing node pixels to 0
    for node in graph.nodes():
        row, col = node
        distance_map[row, col] = 0

    # Initialize R-tree index for spatial queries
    idx = index.Index()
    for i, node in enumerate(graph.nodes()):
        row, col = node
        idx.insert(i, (col, row, col, row))

    # Initialize kernel for dilation
    kernel = np.ones((3, 3), np.uint8)

    iteration = 0
    while True:
        iteration += 1

        # Compute distance transform to nearest node
        distance_map = cv2.distanceTransform(
            (distance_map > 0).astype(np.uint8),
            cv2.DIST_L2,
            cv2.DIST_MASK_PRECISE
        )

        # Identify large distance areas
        large_distance_areas = (distance_map > distance_threshold_px).astype(np.uint8)

        if not np.any(large_distance_areas):
            logger.info(f"Free space sampling converged after {iteration} iterations")
            break

        # Dilate to find local maxima
        dilated = cv2.dilate(distance_map, kernel)

        # Find local maxima
        local_maxima_mask = (distance_map == dilated) & (large_distance_areas > 0)
        local_maxima_coords = np.column_stack(np.where(local_maxima_mask))

        nodes_added_this_iter = 0

        # Add local maxima as nodes
        for coord in local_maxima_coords:
            row, col = coord
            # Check if there are any nodes within distance_threshold/2
            half_threshold = distance_threshold_px / 2
            bounding_box = (
                col - half_threshold,
                row - half_threshold,
                col + half_threshold,
                row + half_threshold
            )
            intersections = list(idx.intersection(bounding_box))

            if len(intersections) == 0:
                graph.add_node((row, col), node_type="free_space")
                idx.insert(len(graph.nodes) - 1, (col, row, col, row))
                distance_map[row, col] = 0
                nodes_added_this_iter += 1

        if nodes_added_this_iter == 0:
            logger.info(f"No new nodes added in iteration {iteration}, stopping")
            break

        logger.debug(f"Iteration {iteration}: added {nodes_added_this_iter} nodes")

    num_nodes_added = len(graph.nodes()) - initial_num_nodes
    logger.info(f"Added {num_nodes_added} free space nodes")
    return num_nodes_added


def main():
    parser = create_step_parser(
        description="Step 4: Sample free space areas",
        requires_map=False
    )
    parser.add_argument(
        "--free-space-sampling-threshold",
        type=float,
        default=1.5,
        help="Maximum distance from obstacles for sampling (meters)"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Save visualization of the graph"
    )
    args = parser.parse_args()

    logger = get_logger(__name__, args.log_level)
    logger.info("=" * 60)
    logger.info("Step 4: Free Space Sampling")
    logger.info("=" * 60)

    # Load previous step data
    step_data = load_step_data(args.input, "step3")

    # Get graph (create new if doesn't exist)
    graph = step_data.graph if step_data.graph is not None else nx.Graph()
    initial_nodes = len(graph.nodes())
    logger.info(f"Starting with {initial_nodes} nodes from previous step")

    # Convert threshold to pixels
    distance_threshold_px = int(args.free_space_sampling_threshold / step_data.resolution)
    logger.info(f"Free space threshold: {args.free_space_sampling_threshold}m = {distance_threshold_px}px")

    # Sample free space
    sample_free_space(
        graph,
        step_data.original_map,
        step_data.occupancy_threshold,
        distance_threshold_px,
        logger
    )

    logger.info(f"Total graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")

    # Save graph
    step_data.graph = graph
    save_step_data(step_data, args.output, "step4")

    # Visualize if requested
    if args.visualize and len(graph.nodes) > 0:
        output_path = f"{args.output}/step4_free_space_sampling.png"
        visualize_graph(graph, step_data.original_map, output_path)

    logger.info("Step 4 complete!")


if __name__ == "__main__":
    main()
