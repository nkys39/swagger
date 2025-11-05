#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Step 1: Preprocess occupancy grid and compute distance transform.

This step:
1. Loads the occupancy grid map
2. Creates a binary free space map based on occupancy threshold
3. Computes distance transform for obstacle avoidance
4. Creates inflated obstacle map based on safety distance
"""

import sys
from pathlib import Path

import cv2
import numpy as np

# Add steps directory to path
sys.path.insert(0, str(Path(__file__).parent))

from common import (
    StepData,
    create_step_parser,
    get_logger,
    load_map,
    save_step_data,
)


def distance_transform(
    free_map: np.ndarray,
    resolution: float,
    safety_distance: float,
    logger
) -> tuple[np.ndarray, np.ndarray]:
    """Compute distance transform and inflate obstacles.

    Args:
        free_map: Binary map where 1 = free, 0 = occupied
        resolution: Map resolution in meters/pixel
        safety_distance: Robot radius in meters
        logger: Logger instance

    Returns:
        Tuple of (distance_transform, inflated_map)
    """
    logger.info("Computing distance transform...")

    # Pad the binary map by 1 pixel on all sides
    free_map_padded = np.pad(free_map, ((1, 1), (1, 1)), mode="constant", constant_values=0)

    # Compute distance transform
    dist_transform = cv2.distanceTransform(free_map_padded, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)

    # Filter by robot's radius to create inflated obstacle map
    inflated_map = (dist_transform < safety_distance / resolution).astype(np.uint8)

    # Unpad to get original map shape
    dist_transform = dist_transform[1:-1, 1:-1]
    inflated_map = inflated_map[1:-1, 1:-1]

    logger.info(f"Distance transform complete")
    return dist_transform, inflated_map


def main():
    parser = create_step_parser(
        description="Step 1: Preprocess map and compute distance transform",
        requires_map=True
    )
    args = parser.parse_args()

    logger = get_logger(__name__, args.log_level)
    logger.info("=" * 60)
    logger.info("Step 1: Preprocessing")
    logger.info("=" * 60)

    # Load map
    logger.info(f"Loading map from {args.map}")
    original_map = load_map(args.map)
    logger.info(f"Map size: {original_map.shape}")

    # Log parameters
    logger.info(f"Parameters:")
    logger.info(f"  Resolution: {args.resolution} m/px")
    logger.info(f"  Safety distance: {args.safety_distance} m")
    logger.info(f"  Occupancy threshold: {args.occupancy_threshold}")

    # Create free space map
    free_map = (original_map > args.occupancy_threshold).astype(np.uint8)
    free_pixels = np.sum(free_map)
    total_pixels = free_map.size
    free_percentage = (free_pixels / total_pixels) * 100
    logger.info(f"Free space: {free_pixels}/{total_pixels} pixels ({free_percentage:.1f}%)")

    # Check if map is completely free
    if np.all(free_map):
        logger.warning("Map is completely free - no obstacles detected!")
        logger.info("Skipping distance transform")
        dist_transform = None
        inflated_map = np.zeros_like(free_map)
    else:
        # Compute distance transform
        dist_transform, inflated_map = distance_transform(
            free_map,
            args.resolution,
            args.safety_distance,
            logger
        )

        # Save distance transform for comparison with C++
        import os
        os.makedirs("debug_output", exist_ok=True)
        np.save("debug_output/python_step1_dist_transform.npy", dist_transform)
        cv2.imwrite("debug_output/python_step1_inflated_map.png", inflated_map)
        logger.info("Saved distance transform to debug_output/ for comparison")

    # Compute transform parameters
    cos_rot = np.cos(args.rotation)
    sin_rot = np.sin(args.rotation)
    image_height = original_map.shape[0]
    y_offset_adjusted = args.y_offset + (image_height * args.resolution)

    # Save data
    step_data = StepData(
        original_map=original_map,
        resolution=args.resolution,
        safety_distance=args.safety_distance,
        occupancy_threshold=args.occupancy_threshold,
        x_offset=args.x_offset,
        y_offset=args.y_offset,
        rotation=args.rotation,
        free_map=free_map,
        dist_transform=dist_transform,
        inflated_map=inflated_map,
        cos_rot=cos_rot,
        sin_rot=sin_rot,
        y_offset_adjusted=y_offset_adjusted,
    )

    save_step_data(step_data, args.output, "step1")
    logger.info("Step 1 complete!")


if __name__ == "__main__":
    main()
