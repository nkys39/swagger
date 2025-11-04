#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Step 2: Generate skeleton graph from the medial axis.

This step:
1. Computes the skeleton (medial axis) of free space
2. Extracts branches from the skeleton
3. Samples nodes along skeleton branches
4. Creates initial graph from skeleton structure
"""

import sys
from pathlib import Path

import networkx as nx
import numpy as np
import skan
from skimage.morphology import skeletonize

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
    """Check if line between two points intersects obstacles.

    Args:
        p0: Start point (y, x)
        p1: End point (y, x)
        inflated_map: Binary map where 1 = obstacle

    Returns:
        True if collision detected, False otherwise
    """
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


def build_skeleton_graph(
    inflated_map: np.ndarray,
    skeleton_sample_distance: int,
    logger
) -> nx.Graph:
    """Generate graph from skeleton of the inflated map.

    Args:
        inflated_map: Binary map where 1 = inflated obstacle
        skeleton_sample_distance: Distance between samples in pixels
        logger: Logger instance

    Returns:
        NetworkX graph with skeleton edges
    """
    logger.info("Computing skeleton using skimage...")
    skeleton_image = skeletonize(1 - inflated_map)

    if skeleton_image.sum() == 0:
        logger.warning("No skeleton found in map")
        return nx.Graph()

    logger.info("Building graph from skeleton branches...")
    skeleton = skan.Skeleton(skeleton_image)
    graph = nx.Graph()

    for i in range(skeleton.n_paths):
        branch = skeleton.path_coordinates(i)
        # Count the number of segments in the branch
        num_segments = max(1, len(branch) // skeleton_sample_distance)
        segment_length = len(branch) // num_segments

        for j in range(num_segments):
            start = branch[j * segment_length]
            end = branch[min((j + 1) * segment_length, len(branch) - 1)]

            if check_line_collision(start, end, inflated_map):
                continue

            dist = np.linalg.norm(end - start)
            graph.add_edge(
                (start[0], start[1]),
                (end[0], end[1]),
                weight=dist,
                edge_type="skeleton"
            )

    logger.info(f"Created skeleton graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    return graph


def main():
    parser = create_step_parser(
        description="Step 2: Generate skeleton graph",
        requires_map=False
    )
    parser.add_argument(
        "--skeleton-sample-distance",
        type=float,
        default=1.5,
        help="Distance between samples along skeleton (meters)"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Save visualization of the graph"
    )
    args = parser.parse_args()

    logger = get_logger(__name__, args.log_level)
    logger.info("=" * 60)
    logger.info("Step 2: Skeleton Graph Generation")
    logger.info("=" * 60)

    # Load previous step data
    step_data = load_step_data(args.input, "step1")

    # Convert distance to pixels
    skeleton_sample_distance_px = int(args.skeleton_sample_distance / step_data.resolution)
    logger.info(f"Skeleton sample distance: {args.skeleton_sample_distance}m ({skeleton_sample_distance_px}px)")

    # Check if map has obstacles
    if step_data.inflated_map is None or np.all(step_data.free_map):
        logger.warning("Map is completely free - creating empty graph")
        graph = nx.Graph()
    else:
        # Build skeleton graph
        graph = build_skeleton_graph(
            step_data.inflated_map,
            skeleton_sample_distance_px,
            logger
        )

    # Save graph
    step_data.graph = graph
    save_step_data(step_data, args.output, "step2")

    # Visualize if requested
    if args.visualize and len(graph.nodes) > 0:
        output_path = f"{args.output}/step2_skeleton_graph.png"
        visualize_graph(graph, step_data.original_map, output_path)

    logger.info("Step 2 complete!")


if __name__ == "__main__":
    main()
