# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import networkx as nx
import numpy as np
import tyro

from swagger import WaypointGraphGenerator, WaypointGraphGeneratorConfig
from swagger.graph_evaluator import WaypointGraphEvaluator
from swagger.logger import Logger
from swagger.performance_evaluator import PerformanceEvaluator

CURRENT_FILE_PATH = Path(__file__).resolve()


@dataclass
class GraphEvalConfig:
    active: bool = False
    num_path_samples: int = 1000  # Number of random paths to sample for evaluation


@dataclass
class PerformanceEvalConfig:
    active: bool = False
    num_query_samples: int = 100  # Number of random queries for performance evaluation


# Define a data class for command line arguments
@dataclass
class Args:
    # Graph generation parameters
    map_path: str = os.path.join(
        CURRENT_FILE_PATH.parent, "../maps/carter_warehouse_navigation.png"
    )  # Path to occupancy grid map image
    resolution: float = 0.05  # Map resolution in meters per pixel
    safety_distance: float = 0.3  # Robot radius in meters
    occupancy_threshold: int = 127  # Occupancy threshold for free space
    x_offset: float = 0.0  # X translation offset in meters
    y_offset: float = 0.0  # Y translation offset in meters
    rotation: float = 0.0  # Rotation in radians
    output_dir: str = "graphs"  # Directory to save output files

    # Algorithm step flags (enable/disable each step)
    use_skeleton_graph: bool = True  # Step 2: Build skeleton graph
    use_boundary_sampling: bool = True  # Step 3: Sample obstacle boundaries
    use_free_space_sampling: bool = True  # Step 4: Sample free space
    use_delaunay_shortcuts: bool = True  # Step 5: Add Delaunay triangulation shortcuts
    prune_graph: bool = True  # Step 6: Prune graph

    # Algorithm parameters (in meters)
    skeleton_sample_distance: float = 1.5  # Distance between skeleton samples
    boundary_inflation_factor: float = 1.5  # Boundary inflation factor
    boundary_sample_distance: float = 2.5  # Distance between boundary samples
    free_space_sampling_threshold: float = 1.5  # Free space sampling threshold
    merge_node_distance: float = 0.25  # Distance to merge nodes
    min_subgraph_length: float = 0.25  # Minimum subgraph length to keep

    # Graph evaluation settings
    graph_eval: GraphEvalConfig = field(default_factory=GraphEvalConfig)

    # Performance evaluation settings
    perf_eval: PerformanceEvalConfig = field(default_factory=PerformanceEvalConfig)


def evaluate_graph(
    graph: nx.Graph,
    occupancy_map: np.ndarray,
    occupancy_threshold: int,
    resolution: float,
    safety_distance: float,
    num_path_samples: int,
    output_dir: str,
    logger: Logger,
):
    # Evaluate the generated graph
    logger.info("Evaluating generated waypoint graph...")
    evaluator = WaypointGraphEvaluator(
        graph=graph,
        occupancy_map=occupancy_map,
        occupancy_threshold=occupancy_threshold,
        resolution=resolution,
        safety_distance=safety_distance,
    )

    metrics = evaluator.evaluate_all(num_path_samples=num_path_samples, print_metrics=True)

    # Save evaluation metrics
    with open(f"{output_dir}/evaluation_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Evaluation metrics saved to {output_dir}/evaluation_metrics.json")


def evaluate_performance(
    generator: WaypointGraphGenerator,
    perf_evaluator: PerformanceEvaluator,
    num_query_samples: int,
    output_dir: str,
    logger: Logger,
):
    """Evaluate and report performance metrics."""
    logger.info("Evaluating performance metrics...")

    # Evaluate query performance
    query_metrics = perf_evaluator.evaluate_query_performance(graph_generator=generator, num_queries=num_query_samples)

    # Get overall performance results
    perf_results = perf_evaluator.get_results()

    # Combine all performance metrics
    performance_metrics = {
        "total_time": perf_results.total_time,
        "peak_memory_mb": perf_results.peak_memory,
        "component_breakdown": perf_results.breakdown,
        "query_performance": query_metrics,
    }

    # Save performance metrics
    with open(f"{output_dir}/performance_metrics.json", "w") as f:
        json.dump(performance_metrics, f, indent=2)

    logger.info(f"Performance metrics saved to {output_dir}/performance_metrics.json")

    # Print performance summary
    print(
        f"""
=== Performance Evaluation Summary ===
Total Execution Time: {perf_results.total_time:.2f} seconds
Peak Memory Usage: {perf_results.peak_memory:.2f} MB

Component Breakdown:
{chr(10).join([f"  - {name}: {duration:.2f} seconds" for name, duration in perf_results.breakdown.items()])}

Query Performance:
  - Average Query Time: {query_metrics['average_query_time']:.6f} seconds
  - Max Query Time: {query_metrics['max_query_time']:.6f} seconds
  - Min Query Time: {query_metrics['min_query_time']:.6f} seconds
  - Total Query Time: {query_metrics['total_query_time']:.6f} seconds
=====================================
"""
    )


@contextmanager
def track_performance(perf_evaluator: PerformanceEvaluator | None, label: str):
    if perf_evaluator:
        perf_evaluator.start(label)
    try:
        yield
    finally:
        if perf_evaluator:
            perf_evaluator.stop(label)


def main():
    # Parse command line arguments using tyro
    args = tyro.cli(Args)
    logger = Logger("generate_graph")

    # Initialize generator with custom configuration from CLI args
    config = WaypointGraphGeneratorConfig(
        # Algorithm step flags
        use_skeleton_graph=args.use_skeleton_graph,
        use_boundary_sampling=args.use_boundary_sampling,
        use_free_space_sampling=args.use_free_space_sampling,
        use_delaunay_shortcuts=args.use_delaunay_shortcuts,
        prune_graph=args.prune_graph,
        # Algorithm parameters
        skeleton_sample_distance=args.skeleton_sample_distance,
        boundary_inflation_factor=args.boundary_inflation_factor,
        boundary_sample_distance=args.boundary_sample_distance,
        free_space_sampling_threshold=args.free_space_sampling_threshold,
        merge_node_distance=args.merge_node_distance,
        min_subgraph_length=args.min_subgraph_length,
    )

    # Log which steps are enabled
    logger.info("Algorithm steps enabled:")
    logger.info(f"  Step 2 - Skeleton graph: {args.use_skeleton_graph}")
    logger.info(f"  Step 3 - Boundary sampling: {args.use_boundary_sampling}")
    logger.info(f"  Step 4 - Free space sampling: {args.use_free_space_sampling}")
    logger.info(f"  Step 5 - Delaunay shortcuts: {args.use_delaunay_shortcuts}")
    logger.info(f"  Step 6 - Graph pruning: {args.prune_graph}")

    generator = WaypointGraphGenerator(config=config)

    # Initialize performance evaluator if needed
    perf_evaluator = None
    if args.perf_eval.active:
        perf_evaluator = PerformanceEvaluator()

    with track_performance(perf_evaluator, "total"):
        # Load map
        logger.info(f"Loading map from {args.map_path}")
        map_path = args.map_path
        if not os.path.exists(map_path):
            raise FileNotFoundError(f"Could not load map file: {map_path}")

        with track_performance(perf_evaluator, "load_map"):
            occupancy_grid = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
            if occupancy_grid is None:
                raise RuntimeError("Failed to read image file")
            logger.info(f"Loaded map with shape: {occupancy_grid.shape}")

        # Set parameters
        resolution = args.resolution  # meters per pixel
        safety_distance = args.safety_distance  # meters
        output_dir = args.output_dir  # Save visualizations to current directory
        os.makedirs(output_dir, exist_ok=True)  # Create output directory if it doesn't exist

        # Generate waypoint graph
        with track_performance(perf_evaluator, "build_graph"):
            graph = generator.build_graph_from_grid_map(
                image=occupancy_grid,
                resolution=resolution,
                safety_distance=safety_distance,
                occupancy_threshold=args.occupancy_threshold,
                x_offset=args.x_offset,
                y_offset=args.y_offset,
                rotation=args.rotation,
            )

        # Save graph to file
        logger.info(f"Saving graph to {output_dir}/graph.gml")
        with track_performance(perf_evaluator, "save_graph"):
            nx.write_gml(graph, f"{output_dir}/graph.gml")

        # Create visualizations
        with track_performance(perf_evaluator, "visualize_graph"):
            generator.visualize_graph(
                output_dir=output_dir,
            )

        if args.graph_eval.active:
            with track_performance(perf_evaluator, "evaluate_graph"):
                evaluate_graph(
                    graph=generator.graph,
                    occupancy_map=occupancy_grid,
                    occupancy_threshold=args.occupancy_threshold,
                    resolution=resolution,
                    safety_distance=safety_distance,
                    num_path_samples=args.graph_eval.num_path_samples,
                    output_dir=output_dir,
                    logger=logger,
                )

    # Evaluate performance if requested
    if args.perf_eval.active:
        evaluate_performance(
            generator=generator,
            perf_evaluator=perf_evaluator,
            num_query_samples=args.perf_eval.num_query_samples,
            output_dir=output_dir,
            logger=logger,
        )


if __name__ == "__main__":
    main()
