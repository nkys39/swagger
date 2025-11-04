#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
Run the complete waypoint graph generation pipeline.

This script orchestrates all 6 steps of the graph generation process:
1. Preprocess map and compute distance transform
2. Generate skeleton graph
3. Sample obstacle boundaries
4. Sample free space areas
5. Add Delaunay shortcuts
6. Prune and finalize graph

You can enable/disable individual steps or run only specific steps.
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from swagger.logger import Logger


def run_step(step_script: str, args: list, logger) -> bool:
    """Run a single step script.

    Args:
        step_script: Path to the step script
        args: Command line arguments to pass
        logger: Logger instance

    Returns:
        True if successful, False otherwise
    """
    cmd = [sys.executable, step_script] + args
    logger.info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Step failed with exit code {e.returncode}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Run complete waypoint graph generation pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all steps
  python run_pipeline.py --map data/map.png --output output/

  # Run only specific steps
  python run_pipeline.py --map data/map.png --output output/ --steps 1,2,5

  # Skip certain steps
  python run_pipeline.py --map data/map.png --output output/ --skip-steps 3,4

  # Enable visualization for all steps
  python run_pipeline.py --map data/map.png --output output/ --visualize-all
        """
    )

    # Input/output arguments
    parser.add_argument("--map", type=str, required=True, help="Path to occupancy grid map")
    parser.add_argument("--output", type=str, default="output", help="Output directory")

    # Map parameters
    parser.add_argument("--resolution", type=float, default=0.05, help="Map resolution (m/px)")
    parser.add_argument("--safety-distance", type=float, default=0.5, help="Robot radius (m)")
    parser.add_argument("--occupancy-threshold", type=int, default=127, help="Occupancy threshold")
    parser.add_argument("--x-offset", type=float, default=0.0, help="X offset (m)")
    parser.add_argument("--y-offset", type=float, default=0.0, help="Y offset (m)")
    parser.add_argument("--rotation", type=float, default=0.0, help="Rotation (radians)")

    # Algorithm parameters
    parser.add_argument("--skeleton-sample-distance", type=float, default=1.5, help="Step 2 parameter (m)")
    parser.add_argument("--boundary-inflation-factor", type=float, default=1.5, help="Step 3 parameter")
    parser.add_argument("--boundary-sample-distance", type=float, default=2.5, help="Step 3 parameter (m)")
    parser.add_argument("--free-space-sampling-threshold", type=float, default=1.5, help="Step 4 parameter (m)")
    parser.add_argument("--merge-node-distance", type=float, default=0.25, help="Step 6 parameter (m)")
    parser.add_argument("--min-subgraph-length", type=float, default=0.25, help="Step 6 parameter (m)")

    # Step control
    parser.add_argument(
        "--steps",
        type=str,
        default="all",
        help="Comma-separated list of steps to run (e.g., '1,2,5' or 'all')"
    )
    parser.add_argument(
        "--skip-steps",
        type=str,
        default="",
        help="Comma-separated list of steps to skip (e.g., '3,4')"
    )

    # Visualization
    parser.add_argument("--visualize-all", action="store_true", help="Visualize output of all steps")

    # Output
    parser.add_argument("--output-graph", type=str, default="final_graph.pkl", help="Final graph filename")

    # Logging
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )

    args = parser.parse_args()

    # Setup logger
    level_map = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING, "ERROR": logging.ERROR}
    logger = Logger(__name__, level=level_map[args.log_level])

    # Determine which steps to run
    if args.steps == "all":
        steps_to_run = {1, 2, 3, 4, 5, 6}
    else:
        try:
            steps_to_run = set(int(s.strip()) for s in args.steps.split(","))
        except ValueError:
            logger.error("Invalid --steps format. Use comma-separated numbers (e.g., '1,2,5')")
            return 1

    # Remove skipped steps
    if args.skip_steps:
        try:
            skip_steps = set(int(s.strip()) for s in args.skip_steps.split(","))
            steps_to_run -= skip_steps
        except ValueError:
            logger.error("Invalid --skip-steps format. Use comma-separated numbers (e.g., '3,4')")
            return 1

    logger.info("=" * 60)
    logger.info("Waypoint Graph Generation Pipeline")
    logger.info("=" * 60)
    logger.info(f"Steps to run: {sorted(steps_to_run)}")

    # Get script directory
    script_dir = Path(__file__).parent / "steps"

    # Step configurations
    step_configs = {
        1: {
            "script": script_dir / "step1_preprocess.py",
            "args": [
                "--map", args.map,
                "--resolution", str(args.resolution),
                "--safety-distance", str(args.safety_distance),
                "--occupancy-threshold", str(args.occupancy_threshold),
                "--x-offset", str(args.x_offset),
                "--y-offset", str(args.y_offset),
                "--rotation", str(args.rotation),
                "--output", args.output,
                "--log-level", args.log_level,
            ],
        },
        2: {
            "script": script_dir / "step2_skeleton_graph.py",
            "args": [
                "--input", args.output,
                "--output", args.output,
                "--skeleton-sample-distance", str(args.skeleton_sample_distance),
                "--log-level", args.log_level,
            ],
        },
        3: {
            "script": script_dir / "step3_boundary_sampling.py",
            "args": [
                "--input", args.output,
                "--output", args.output,
                "--boundary-inflation-factor", str(args.boundary_inflation_factor),
                "--boundary-sample-distance", str(args.boundary_sample_distance),
                "--log-level", args.log_level,
            ],
        },
        4: {
            "script": script_dir / "step4_free_space_sampling.py",
            "args": [
                "--input", args.output,
                "--output", args.output,
                "--free-space-sampling-threshold", str(args.free_space_sampling_threshold),
                "--log-level", args.log_level,
            ],
        },
        5: {
            "script": script_dir / "step5_delaunay_shortcuts.py",
            "args": [
                "--input", args.output,
                "--output", args.output,
                "--log-level", args.log_level,
            ],
        },
        6: {
            "script": script_dir / "step6_prune_graph.py",
            "args": [
                "--input", args.output,
                "--output", args.output,
                "--merge-node-distance", str(args.merge_node_distance),
                "--min-subgraph-length", str(args.min_subgraph_length),
                "--output-graph", args.output_graph,
                "--log-level", args.log_level,
            ],
        },
    }

    # Add visualization flag if requested
    if args.visualize_all:
        for step in [2, 3, 4, 5, 6]:
            if step in step_configs:
                step_configs[step]["args"].append("--visualize")

    # Run steps in order
    for step_num in sorted(steps_to_run):
        if step_num not in step_configs:
            logger.error(f"Invalid step number: {step_num}")
            return 1

        config = step_configs[step_num]
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"Running Step {step_num}")
        logger.info("=" * 60)

        success = run_step(str(config["script"]), config["args"], logger)

        if not success:
            logger.error(f"Step {step_num} failed. Stopping pipeline.")
            return 1

    logger.info("")
    logger.info("=" * 60)
    logger.info("Pipeline completed successfully!")
    logger.info("=" * 60)
    logger.info(f"Output directory: {args.output}")
    logger.info(f"Final graph: {args.output}/{args.output_graph}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
