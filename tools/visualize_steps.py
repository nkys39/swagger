#!/usr/bin/env python3
"""Visualize each step of graph generation for C++ and Python comparison."""

import sys
import numpy as np
import cv2
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from swagger.waypoint_graph_generator import WaypointGraphGenerator, WaypointGraphGeneratorConfig


def draw_graph_on_map(image, graph, title, node_color=(0, 0, 255), edge_color=(255, 0, 0), node_radius=3):
    """Draw graph nodes and edges on map image."""
    # Convert grayscale to BGR
    vis = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    # Draw edges first (so they appear under nodes)
    for edge in graph.edges():
        node1_id, node2_id = edge
        pixel1 = graph.nodes[node1_id]['pixel']
        pixel2 = graph.nodes[node2_id]['pixel']

        p1 = (int(pixel1[1]), int(pixel1[0]))  # (col, row) -> (x, y)
        p2 = (int(pixel2[1]), int(pixel2[0]))

        cv2.line(vis, p1, p2, edge_color, 1, cv2.LINE_AA)

    # Draw nodes on top
    for node_id in graph.nodes():
        pixel = graph.nodes[node_id]['pixel']
        center = (int(pixel[1]), int(pixel[0]))  # (col, row) -> (x, y)
        cv2.circle(vis, center, node_radius, node_color, -1, cv2.LINE_AA)

    # Add title
    cv2.putText(vis, title, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)

    # Add node/edge count
    info_text = f"Nodes: {len(graph.nodes())}, Edges: {len(graph.edges())}"
    cv2.putText(vis, info_text, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)

    return vis


def visualize_python_steps(image, resolution, safety_distance, occupancy_threshold, output_dir):
    """Generate and visualize Python graph at each step."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print("\n" + "=" * 80)
    print("Generating Python Step-by-Step Visualizations")
    print("=" * 80)

    steps = [
        ("step2", "Step 2: Skeleton", {
            'use_skeleton_graph': True,
            'use_boundary_sampling': False,
            'use_free_space_sampling': False,
            'use_delaunay_shortcuts': False,
            'prune_graph': False,
        }),
        ("step3", "Step 3: + Boundary", {
            'use_skeleton_graph': True,
            'use_boundary_sampling': True,
            'use_free_space_sampling': False,
            'use_delaunay_shortcuts': False,
            'prune_graph': False,
        }),
        ("step4", "Step 4: + Free Space", {
            'use_skeleton_graph': True,
            'use_boundary_sampling': True,
            'use_free_space_sampling': True,
            'use_delaunay_shortcuts': False,
            'prune_graph': False,
        }),
        ("step5", "Step 5: + Delaunay", {
            'use_skeleton_graph': True,
            'use_boundary_sampling': True,
            'use_free_space_sampling': True,
            'use_delaunay_shortcuts': True,
            'prune_graph': False,
        }),
        ("step6", "Step 6: + Pruning", {
            'use_skeleton_graph': True,
            'use_boundary_sampling': True,
            'use_free_space_sampling': True,
            'use_delaunay_shortcuts': True,
            'prune_graph': True,
        }),
    ]

    for step_name, title, config_overrides in steps:
        print(f"\nGenerating {title}...")

        # Create config
        config = WaypointGraphGeneratorConfig(
            skeleton_sample_distance=1.5,
            boundary_inflation_factor=1.5,
            boundary_sample_distance=2.5,
            free_space_sampling_threshold=1.5,
            merge_node_distance=0.25,
            min_subgraph_length=0.25,
            **config_overrides
        )

        # Generate graph
        generator = WaypointGraphGenerator(config=config)
        graph = generator.build_graph_from_grid_map(
            image=image,
            resolution=resolution,
            safety_distance=safety_distance,
            occupancy_threshold=occupancy_threshold,
        )

        # Visualize
        vis = draw_graph_on_map(image, graph, f"Python {title}")

        # Save
        output_file = output_path / f"python_{step_name}.png"
        cv2.imwrite(str(output_file), vis)
        print(f"  Saved: {output_file}")
        print(f"  Nodes: {len(graph.nodes())}, Edges: {len(graph.edges())}")


def create_comparison_grid(output_dir):
    """Create a grid comparison image of all steps."""
    output_path = Path(output_dir)

    print("\n" + "=" * 80)
    print("Creating Comparison Grid")
    print("=" * 80)

    steps = ["step2", "step3", "step4", "step5", "step6"]

    # Load all Python images
    python_images = []
    for step in steps:
        img_path = output_path / f"python_{step}.png"
        if img_path.exists():
            img = cv2.imread(str(img_path))
            python_images.append(img)
        else:
            print(f"Warning: {img_path} not found")

    if not python_images:
        print("Error: No images to create grid")
        return

    # Create vertical stack
    grid = np.vstack(python_images)

    # Save grid
    grid_path = output_path / "python_all_steps.png"
    cv2.imwrite(str(grid_path), grid)
    print(f"Saved comparison grid: {grid_path}")


def main():
    # Test parameters
    map_path = "maps/carter_warehouse_navigation.png"
    resolution = 0.05
    safety_distance = 0.3
    occupancy_threshold = 127
    output_dir = "visualization_output"

    print("=" * 80)
    print("Step-by-Step Visualization Generator")
    print("=" * 80)
    print(f"\nParameters:")
    print(f"  map: {map_path}")
    print(f"  resolution: {resolution}m/px")
    print(f"  safety_distance: {safety_distance}m")
    print(f"  occupancy_threshold: {occupancy_threshold}")
    print(f"  output_dir: {output_dir}")

    # Load map
    image = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        print(f"Error: Could not load map: {map_path}")
        return 1

    # Generate Python visualizations
    visualize_python_steps(image, resolution, safety_distance, occupancy_threshold, output_dir)

    # Create comparison grid
    create_comparison_grid(output_dir)

    print("\n" + "=" * 80)
    print("Visualization Complete!")
    print("=" * 80)
    print(f"\nGenerated files in '{output_dir}/':")
    print("  - python_step2.png  (Skeleton only)")
    print("  - python_step3.png  (+ Boundary)")
    print("  - python_step4.png  (+ Free Space)")
    print("  - python_step5.png  (+ Delaunay)")
    print("  - python_step6.png  (+ Pruning)")
    print("  - python_all_steps.png  (All steps in one image)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
