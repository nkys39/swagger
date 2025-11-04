#!/usr/bin/env python3
"""Test script to compare C++ and Python implementations."""

import sys
import numpy as np
import cv2
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from swagger.waypoint_graph_generator import WaypointGraphGenerator, WaypointGraphGeneratorConfig


def print_graph_stats(graph, step_name):
    """Print detailed graph statistics."""
    print(f"\n{'━' * 60}")
    print(f"📊 {step_name} 詳細統計")
    print(f"{'━' * 60}")

    # Node statistics
    num_nodes = len(graph.nodes())
    print(f"ノード数: {num_nodes}")

    if num_nodes > 0:
        # Count nodes by type
        node_types = {}
        for node, data in graph.nodes(data=True):
            node_type = data.get('node_type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1

        if node_types:
            print("  ノードタイプ別:")
            for node_type, count in sorted(node_types.items()):
                print(f"    - {node_type}: {count}")

    # Edge statistics
    num_edges = len(graph.edges())
    print(f"エッジ数: {num_edges}")

    if num_edges > 0:
        # Count edges by type
        edge_types = {}
        edge_lengths = {}

        for u, v, data in graph.edges(data=True):
            edge_type = data.get('edge_type', 'unknown')
            weight = data.get('weight', 0)

            edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
            if edge_type not in edge_lengths:
                edge_lengths[edge_type] = []
            edge_lengths[edge_type].append(weight)

        if edge_types:
            print("  エッジタイプ別:")
            total_length = 0
            for edge_type, count in sorted(edge_types.items()):
                lengths = edge_lengths[edge_type]
                avg_length = np.mean(lengths)
                total_length += sum(lengths)
                print(f"    - {edge_type}: {count} 個 (平均長: {avg_length:.2f} px)")

            print(f"  総エッジ長: {total_length:.2f} px")

    # Sample nodes
    if num_nodes > 0:
        print("\nサンプルノード (最初の3個):")
        for i, (node, data) in enumerate(list(graph.nodes(data=True))[:3]):
            node_type = data.get('node_type', 'unknown')
            print(f"  ノード[{i}]: {node} - {node_type}")

    print(f"{'━' * 60}\n")


def main():
    # Test parameters (matching C++ test)
    map_path = "maps/carter_warehouse_navigation.png"
    resolution = 0.05
    safety_distance = 0.3
    occupancy_threshold = 127

    print("=" * 60)
    print("SWAGGER Python: 完全実装版（Step 1-6）")
    print("=" * 60)

    # Load map
    print("\nマップを読み込み中:", map_path)
    image = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        print(f"エラー: マップを読み込めませんでした: {map_path}")
        return 1

    print(f"マップサイズ: {image.shape[1]}x{image.shape[0]}")
    print(f"パラメータ:")
    print(f"  解像度: {resolution} m/px")
    print(f"  安全距離: {safety_distance} m")
    print(f"  占有閾値: {occupancy_threshold}")

    # Configure generator
    config = WaypointGraphGeneratorConfig(
        skeleton_sample_distance=1.5,
        boundary_inflation_factor=1.5,
        boundary_sample_distance=2.5,
        free_space_sampling_threshold=1.5,
        merge_node_distance=0.25,
        min_subgraph_length=0.25,
        use_skeleton_graph=True,
        use_boundary_sampling=True,
        use_free_space_sampling=True,
        use_delaunay_shortcuts=True,
        prune_graph=True,
    )

    generator = WaypointGraphGenerator(config=config)

    # Build graph
    print("\nグラフ生成を開始...")
    graph = generator.build_graph_from_grid_map(
        image=image,
        resolution=resolution,
        safety_distance=safety_distance,
        occupancy_threshold=occupancy_threshold,
    )

    # Print final statistics
    print_graph_stats(graph, "最終結果")

    print("=" * 60)
    print("処理完了！")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
