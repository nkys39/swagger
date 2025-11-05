#!/usr/bin/env python3
"""Compare C++ and Python implementations step by step."""

import sys
import json
import numpy as np
import cv2
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from swagger.waypoint_graph_generator import WaypointGraphGenerator, WaypointGraphGeneratorConfig


def analyze_cpp_output(json_path):
    """Load and analyze C++ JSON output."""
    if not Path(json_path).exists():
        return None

    with open(json_path, 'r') as f:
        data = json.load(f)

    # Count nodes by type
    node_types = {}
    for node_data in data.get('nodes', []):
        node_type = node_data.get('node_type', 'unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1

    return {
        'total_nodes': len(data.get('nodes', [])),
        'total_edges': len(data.get('edges', [])),
        'node_types': node_types
    }


def analyze_python_step_by_step(image, resolution, safety_distance, occupancy_threshold):
    """Generate Python graph step by step and analyze each stage."""
    results = {}

    # Configure generator WITHOUT pruning first
    config = WaypointGraphGeneratorConfig(
        skeleton_sample_distance=1.5,
        boundary_inflation_factor=1.5,
        boundary_sample_distance=2.5,
        free_space_sampling_threshold=1.5,
        merge_node_distance=0.25,
        min_subgraph_length=0.25,
        use_skeleton_graph=True,
        use_boundary_sampling=False,  # Disable step 3
        use_free_space_sampling=False,  # Disable step 4
        use_delaunay_shortcuts=False,  # Disable step 5
        prune_graph=False,  # Disable step 6
    )

    generator = WaypointGraphGenerator(config=config)

    # Step 2: Skeleton only
    print("\n" + "=" * 80)
    print("Python Step 2: Skeleton")
    print("=" * 80)
    graph = generator.build_graph_from_grid_map(
        image=image,
        resolution=resolution,
        safety_distance=safety_distance,
        occupancy_threshold=occupancy_threshold,
    )

    # Count node types
    node_types = {}
    for node_id in graph.nodes():
        node_type = graph.nodes[node_id].get('node_type', 'unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1

    results['step2'] = {
        'total_nodes': len(graph.nodes()),
        'total_edges': len(graph.edges()),
        'node_types': node_types
    }
    print(f"Nodes: {len(graph.nodes())}, Edges: {len(graph.edges())}")
    print(f"Node types: {node_types}")

    # Step 3: Add boundary
    print("\n" + "=" * 80)
    print("Python Step 3: + Boundary")
    print("=" * 80)
    config.use_boundary_sampling = True
    generator = WaypointGraphGenerator(config=config)
    graph = generator.build_graph_from_grid_map(
        image=image,
        resolution=resolution,
        safety_distance=safety_distance,
        occupancy_threshold=occupancy_threshold,
    )

    node_types = {}
    for node_id in graph.nodes():
        node_type = graph.nodes[node_id].get('node_type', 'unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1

    results['step3'] = {
        'total_nodes': len(graph.nodes()),
        'total_edges': len(graph.edges()),
        'node_types': node_types
    }
    print(f"Nodes: {len(graph.nodes())}, Edges: {len(graph.edges())}")
    print(f"Node types: {node_types}")

    # Step 4: Add free space
    print("\n" + "=" * 80)
    print("Python Step 4: + Free Space")
    print("=" * 80)
    config.use_free_space_sampling = True
    generator = WaypointGraphGenerator(config=config)
    graph = generator.build_graph_from_grid_map(
        image=image,
        resolution=resolution,
        safety_distance=safety_distance,
        occupancy_threshold=occupancy_threshold,
    )

    node_types = {}
    for node_id in graph.nodes():
        node_type = graph.nodes[node_id].get('node_type', 'unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1

    results['step4'] = {
        'total_nodes': len(graph.nodes()),
        'total_edges': len(graph.edges()),
        'node_types': node_types
    }
    print(f"Nodes: {len(graph.nodes())}, Edges: {len(graph.edges())}")
    print(f"Node types: {node_types}")

    # Step 5: Add Delaunay
    print("\n" + "=" * 80)
    print("Python Step 5: + Delaunay")
    print("=" * 80)
    config.use_delaunay_shortcuts = True
    generator = WaypointGraphGenerator(config=config)
    graph = generator.build_graph_from_grid_map(
        image=image,
        resolution=resolution,
        safety_distance=safety_distance,
        occupancy_threshold=occupancy_threshold,
    )

    node_types = {}
    for node_id in graph.nodes():
        node_type = graph.nodes[node_id].get('node_type', 'unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1

    results['step5'] = {
        'total_nodes': len(graph.nodes()),
        'total_edges': len(graph.edges()),
        'node_types': node_types
    }
    print(f"Nodes: {len(graph.nodes())}, Edges: {len(graph.edges())}")
    print(f"Node types: {node_types}")

    # Step 6: Pruning
    print("\n" + "=" * 80)
    print("Python Step 6: + Pruning")
    print("=" * 80)
    config.prune_graph = True
    generator = WaypointGraphGenerator(config=config)
    graph = generator.build_graph_from_grid_map(
        image=image,
        resolution=resolution,
        safety_distance=safety_distance,
        occupancy_threshold=occupancy_threshold,
    )

    node_types = {}
    for node_id in graph.nodes():
        node_type = graph.nodes[node_id].get('node_type', 'unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1

    results['step6'] = {
        'total_nodes': len(graph.nodes()),
        'total_edges': len(graph.edges()),
        'node_types': node_types
    }
    print(f"Nodes: {len(graph.nodes())}, Edges: {len(graph.edges())}")
    print(f"Node types: {node_types}")

    return results


def main():
    # Test parameters
    map_path = "maps/carter_warehouse_navigation.png"
    resolution = 0.05
    safety_distance = 0.3
    occupancy_threshold = 127

    print("=" * 80)
    print("Step-by-Step Comparison: C++ vs Python")
    print("=" * 80)
    print(f"\nParameters:")
    print(f"  map: {map_path}")
    print(f"  resolution: {resolution}m/px")
    print(f"  safety_distance: {safety_distance}m")
    print(f"  occupancy_threshold: {occupancy_threshold}")

    # Load map
    image = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        print(f"Error: Could not load map: {map_path}")
        return 1

    # Analyze Python step by step
    python_results = analyze_python_step_by_step(image, resolution, safety_distance, occupancy_threshold)

    # Load C++ final result
    print("\n" + "=" * 80)
    print("C++ Final Result (Step 6)")
    print("=" * 80)
    cpp_result = analyze_cpp_output("output/waypoint_graph.json")
    if cpp_result:
        print(f"Nodes: {cpp_result['total_nodes']}, Edges: {cpp_result['total_edges']}")
        print(f"Node types: {cpp_result['node_types']}")
    else:
        print("C++ output not found. Please run C++ version first.")
        cpp_result = None

    # Summary comparison
    print("\n" + "=" * 80)
    print("SUMMARY COMPARISON")
    print("=" * 80)

    steps = ['step2', 'step3', 'step4', 'step5', 'step6']
    step_names = ['Step 2 (Skeleton)', 'Step 3 (+ Boundary)', 'Step 4 (+ Free Space)',
                  'Step 5 (+ Delaunay)', 'Step 6 (+ Pruning)']

    print(f"\n{'Step':<25} {'Python Nodes':<15} {'C++ Nodes':<15} {'Difference':<15}")
    print("-" * 70)

    for step, name in zip(steps, step_names):
        py_nodes = python_results[step]['total_nodes']

        if step == 'step6' and cpp_result:
            cpp_nodes = cpp_result['total_nodes']
            diff = cpp_nodes - py_nodes
            diff_pct = (diff / py_nodes * 100) if py_nodes > 0 else 0
            print(f"{name:<25} {py_nodes:<15} {cpp_nodes:<15} {diff:+d} ({diff_pct:+.1f}%)")
        else:
            print(f"{name:<25} {py_nodes:<15} {'N/A':<15} {'N/A':<15}")

    # Detailed node type comparison
    if cpp_result:
        print("\n" + "=" * 80)
        print("NODE TYPE BREAKDOWN (Final)")
        print("=" * 80)

        py_types = python_results['step6']['node_types']
        cpp_types = cpp_result['node_types']

        all_types = set(py_types.keys()) | set(cpp_types.keys())

        print(f"\n{'Node Type':<20} {'Python':<15} {'C++':<15} {'Difference':<15}")
        print("-" * 65)

        for node_type in sorted(all_types):
            py_count = py_types.get(node_type, 0)
            cpp_count = cpp_types.get(node_type, 0)
            diff = cpp_count - py_count
            print(f"{node_type:<20} {py_count:<15} {cpp_count:<15} {diff:+d}")

        print("-" * 65)
        py_total = sum(py_types.values())
        cpp_total = sum(cpp_types.values())
        total_diff = cpp_total - py_total
        print(f"{'TOTAL':<20} {py_total:<15} {cpp_total:<15} {total_diff:+d}")

    print("\n" + "=" * 80)
    print("Analysis Complete!")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
