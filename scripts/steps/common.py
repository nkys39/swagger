# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Common utilities for modular graph generation steps."""

import argparse
import logging
import os
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import cv2
import networkx as nx
import numpy as np

from swagger.logger import Logger


@dataclass
class StepData:
    """Container for intermediate data passed between steps."""

    # Original map data
    original_map: np.ndarray
    resolution: float
    safety_distance: float
    occupancy_threshold: int
    x_offset: float
    y_offset: float
    rotation: float

    # Processed map data
    free_map: Optional[np.ndarray] = None
    dist_transform: Optional[np.ndarray] = None
    inflated_map: Optional[np.ndarray] = None

    # Graph data
    graph: Optional[nx.Graph] = None

    # Transform parameters
    cos_rot: Optional[float] = None
    sin_rot: Optional[float] = None
    y_offset_adjusted: Optional[float] = None


def load_map(map_path: str) -> np.ndarray:
    """Load an occupancy grid map from a file.

    Args:
        map_path: Path to the map image file

    Returns:
        Occupancy grid as numpy array
    """
    if not os.path.exists(map_path):
        raise FileNotFoundError(f"Map file not found: {map_path}")

    occupancy_grid = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
    if occupancy_grid is None:
        raise ValueError(f"Failed to load map from {map_path}")

    return occupancy_grid


def save_step_data(data: StepData, output_dir: str, step_name: str) -> None:
    """Save intermediate step data to disk.

    Args:
        data: StepData object to save
        output_dir: Directory to save data to
        step_name: Name of the step (e.g., 'step1', 'step2')
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{step_name}_data.pkl")

    with open(output_path, 'wb') as f:
        pickle.dump(data, f)

    print(f"Saved {step_name} data to {output_path}")


def load_step_data(output_dir: str, step_name: str) -> StepData:
    """Load intermediate step data from disk.

    Args:
        output_dir: Directory containing saved data
        step_name: Name of the step (e.g., 'step1', 'step2')

    Returns:
        StepData object
    """
    input_path = os.path.join(output_dir, f"{step_name}_data.pkl")

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Step data not found: {input_path}")

    with open(input_path, 'rb') as f:
        data = pickle.load(f)

    print(f"Loaded {step_name} data from {input_path}")
    return data


def save_graph(graph: nx.Graph, output_dir: str, filename: str = "graph.pkl") -> None:
    """Save a NetworkX graph to disk.

    Args:
        graph: NetworkX graph to save
        output_dir: Directory to save graph to
        filename: Output filename
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    with open(output_path, 'wb') as f:
        pickle.dump(graph, f)

    print(f"Saved graph to {output_path}")


def load_graph(output_dir: str, filename: str = "graph.pkl") -> nx.Graph:
    """Load a NetworkX graph from disk.

    Args:
        output_dir: Directory containing the graph
        filename: Graph filename

    Returns:
        NetworkX graph
    """
    input_path = os.path.join(output_dir, filename)

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Graph file not found: {input_path}")

    with open(input_path, 'rb') as f:
        graph = pickle.load(f)

    print(f"Loaded graph from {input_path}")
    return graph


def create_base_parser(description: str) -> argparse.ArgumentParser:
    """Create argument parser with common arguments.

    Args:
        description: Description for the parser

    Returns:
        ArgumentParser with common arguments
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="Output directory for intermediate data"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    return parser


def create_step_parser(description: str, requires_map: bool = False) -> argparse.ArgumentParser:
    """Create argument parser for a step script.

    Args:
        description: Description for the parser
        requires_map: Whether this step requires map input

    Returns:
        ArgumentParser configured for a step
    """
    parser = create_base_parser(description)

    if requires_map:
        parser.add_argument(
            "--map",
            type=str,
            required=True,
            help="Path to occupancy grid map (PNG/PGM)"
        )
        parser.add_argument(
            "--resolution",
            type=float,
            default=0.05,
            help="Map resolution in meters/pixel"
        )
        parser.add_argument(
            "--safety-distance",
            type=float,
            default=0.5,
            help="Robot radius in meters"
        )
        parser.add_argument(
            "--occupancy-threshold",
            type=int,
            default=127,
            help="Occupancy threshold (0-255)"
        )
        parser.add_argument(
            "--x-offset",
            type=float,
            default=0.0,
            help="X offset in meters"
        )
        parser.add_argument(
            "--y-offset",
            type=float,
            default=0.0,
            help="Y offset in meters"
        )
        parser.add_argument(
            "--rotation",
            type=float,
            default=0.0,
            help="Rotation in radians"
        )
    else:
        parser.add_argument(
            "--input",
            type=str,
            required=True,
            help="Input directory containing previous step data"
        )

    return parser


def get_logger(name: str, level: str = "INFO") -> Logger:
    """Get a logger instance.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Logger instance
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }
    return Logger(name, level=level_map[level])


def visualize_graph(
    graph: nx.Graph,
    original_map: np.ndarray,
    output_path: str,
    edge_color: tuple = (0, 0, 255),
    node_color: tuple = (255, 0, 0)
) -> None:
    """Visualize a graph on the original map.

    Args:
        graph: NetworkX graph with 'pixel' attributes
        original_map: Original occupancy grid
        output_path: Path to save visualization
        edge_color: RGB color for edges
        node_color: RGB color for nodes
    """
    # Convert to BGR for visualization
    map_vis = cv2.cvtColor(original_map, cv2.COLOR_GRAY2BGR)

    # Draw edges
    lines = []
    for src, dst in graph.edges():
        src_pixel = graph.nodes[src]["pixel"]
        dst_pixel = graph.nodes[dst]["pixel"]
        lines.append([[src_pixel[1], src_pixel[0]], [dst_pixel[1], dst_pixel[0]]])

    if lines:
        lines = np.array(lines)
        cv2.polylines(map_vis, lines, False, edge_color, 1)

    # Draw nodes
    node_radius = 2
    for _, pixel in graph.nodes(data="pixel"):
        y, x = pixel
        cv2.circle(map_vis, (x, y), node_radius, node_color, -1)

    # Save
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    if not cv2.imwrite(output_path, map_vis):
        raise RuntimeError(f"Failed to save visualization to {output_path}")

    print(f"Saved visualization to {output_path}")
