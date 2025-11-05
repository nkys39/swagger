#!/usr/bin/env python3
"""Compare final graph outputs from C++ and Python implementations."""

import sys
import json
import numpy as np
import cv2
from pathlib import Path
from scipy.spatial import cKDTree

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from swagger.waypoint_graph_generator import WaypointGraphGenerator, WaypointGraphGeneratorConfig


def load_cpp_graph(json_path):
    """Load graph from C++ JSON output."""
    with open(json_path, 'r') as f:
        data = json.load(f)

    nodes = []
    for node_data in data.get('nodes', []):
        # Extract pixel coordinates from C++ output
        pixel = node_data.get('pixel', {})
        row = pixel.get('row', 0)
        col = pixel.get('col', 0)
        nodes.append((row, col))

    return np.array(nodes)


def analyze_graph_spacing(nodes, name, merge_threshold_px):
    """Analyze spacing between nodes in a graph."""
    print(f"\n{name}:")
    print(f"  総ノード数: {len(nodes)}")

    if len(nodes) < 2:
        return

    tree = cKDTree(nodes)

    # Find all pairs within merge threshold
    pairs = tree.query_pairs(r=merge_threshold_px)
    print(f"  merge_threshold ({merge_threshold_px:.1f}px) 内のペア数: {len(pairs)}")

    if len(pairs) > 0:
        print(f"  ⚠️  警告: {len(pairs)} 個の近接ペアが統合されずに残っています！")

        # Show first few pairs
        print(f"\n  最初の5ペアの詳細:")
        for i, (idx1, idx2) in enumerate(list(pairs)[:5]):
            n1 = nodes[idx1]
            n2 = nodes[idx2]
            dist = np.linalg.norm(n1 - n2)
            print(f"    [{i}] ({n1[0]}, {n1[1]}) ↔ ({n2[0]}, {n2[1]}): {dist:.2f}px")

    # Calculate nearest neighbor distances
    all_distances = []
    for i in range(len(nodes)):
        # Find k=2 to get distance to nearest neighbor (k=1 is self)
        distances, _ = tree.query(nodes[i], k=2)
        all_distances.append(distances[1])  # Second nearest is the closest neighbor

    all_distances = np.array(all_distances)

    print(f"\n  最近傍距離の統計:")
    print(f"    平均: {np.mean(all_distances):.2f}px")
    print(f"    中央値: {np.median(all_distances):.2f}px")
    print(f"    最小: {np.min(all_distances):.2f}px")
    print(f"    最大: {np.max(all_distances):.2f}px")
    print(f"    5パーセンタイル: {np.percentile(all_distances, 5):.2f}px")

    # Count nodes with very close neighbors
    very_close = np.sum(all_distances < merge_threshold_px)
    print(f"\n  merge_threshold以下の最近傍を持つノード: {very_close} ({very_close/len(nodes)*100:.1f}%)")


def compare_graphs(cpp_nodes, python_nodes, merge_threshold_px):
    """Compare C++ and Python graph outputs."""
    print("\n" + "=" * 80)
    print("グラフ比較分析")
    print("=" * 80)

    analyze_graph_spacing(cpp_nodes, "C++グラフ", merge_threshold_px)
    analyze_graph_spacing(python_nodes, "Pythonグラフ", merge_threshold_px)

    # Overall comparison
    print("\n" + "=" * 80)
    print("総合比較:")
    print("=" * 80)
    print(f"  C++ノード数: {len(cpp_nodes)}")
    print(f"  Pythonノード数: {len(python_nodes)}")
    diff_pct = (len(cpp_nodes) - len(python_nodes)) / len(python_nodes) * 100
    print(f"  差分: {len(cpp_nodes) - len(python_nodes)} ノード ({diff_pct:+.1f}%)")


def main():
    # Test parameters
    map_path = "maps/carter_warehouse_navigation.png"
    resolution = 0.05
    safety_distance = 0.3
    occupancy_threshold = 127
    merge_node_distance = 0.25

    merge_threshold_px = merge_node_distance / resolution  # 5 pixels

    print("=" * 80)
    print("C++ vs Python 最終グラフ比較")
    print("=" * 80)
    print(f"\nパラメータ:")
    print(f"  merge_node_distance: {merge_node_distance}m = {merge_threshold_px:.1f}px")

    # Generate Python graph
    print("\n" + "-" * 80)
    print("Pythonグラフを生成中...")
    print("-" * 80)

    image = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        print(f"エラー: マップを読み込めませんでした: {map_path}")
        return 1

    config = WaypointGraphGeneratorConfig(
        skeleton_sample_distance=1.5,
        boundary_inflation_factor=1.5,
        boundary_sample_distance=2.5,
        free_space_sampling_threshold=1.5,
        merge_node_distance=merge_node_distance,
        min_subgraph_length=0.25,
        use_skeleton_graph=True,
        use_boundary_sampling=True,
        use_free_space_sampling=True,
        use_delaunay_shortcuts=True,
        prune_graph=True,
    )

    generator = WaypointGraphGenerator(config=config)
    python_graph = generator.build_graph_from_grid_map(
        image=image,
        resolution=resolution,
        safety_distance=safety_distance,
        occupancy_threshold=occupancy_threshold,
    )

    python_nodes = np.array(list(python_graph.nodes()))
    print(f"Python完了: {len(python_nodes)} ノード")

    # Load C++ graph from JSON
    cpp_json_path = "output_cpp/waypoint_graph.json"

    print("\n" + "-" * 80)
    print(f"C++グラフを読み込み中: {cpp_json_path}")
    print("-" * 80)

    if not Path(cpp_json_path).exists():
        print(f"エラー: {cpp_json_path} が見つかりません")
        print(f"\n先にC++版を実行してください:")
        print(f"  cd swagger-cpp/build")
        print(f"  ./generate_graph --map ../../maps/carter_warehouse_navigation.png --safety-distance 0.3")
        return 1

    cpp_nodes = load_cpp_graph(cpp_json_path)
    print(f"C++完了: {len(cpp_nodes)} ノード")

    # Compare
    compare_graphs(cpp_nodes, python_nodes, merge_threshold_px)

    print("\n" + "=" * 80)
    print("分析完了！")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
