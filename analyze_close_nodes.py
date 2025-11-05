#!/usr/bin/env python3
"""Analyze close nodes in the final graph to understand pruning differences."""

import sys
import numpy as np
import cv2
from pathlib import Path
from scipy.spatial import cKDTree

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from swagger.waypoint_graph_generator import WaypointGraphGenerator, WaypointGraphGeneratorConfig


def analyze_close_nodes(graph, merge_threshold_px):
    """Find pairs of nodes that are close but not merged."""
    nodes = list(graph.nodes())
    if len(nodes) < 2:
        return []

    node_coords = np.array(nodes)
    tree = cKDTree(node_coords)

    # Find all pairs within merge threshold
    pairs = tree.query_pairs(r=merge_threshold_px)

    print(f"\n近接ノードペア分析（merge_threshold = {merge_threshold_px:.1f}px）:")
    print(f"  総ノード数: {len(nodes)}")
    print(f"  merge_threshold内のペア数: {len(pairs)}")

    if len(pairs) > 0:
        print(f"\n  最初の10ペアの詳細:")
        for i, (idx1, idx2) in enumerate(list(pairs)[:10]):
            n1 = nodes[idx1]
            n2 = nodes[idx2]
            dist = np.sqrt((n1[0] - n2[0])**2 + (n1[1] - n2[1])**2)

            # Check connectivity
            n1_neighbors = list(graph.neighbors(n1))
            n2_neighbors = list(graph.neighbors(n2))
            are_connected = n2 in n1_neighbors

            print(f"    [{i}] {n1} ↔ {n2}: distance={dist:.2f}px, connected={are_connected}")
            print(f"        n1 neighbors: {len(n1_neighbors)}, n2 neighbors: {len(n2_neighbors)}")

    return pairs


def main():
    # Test parameters (matching C++ test)
    map_path = "maps/carter_warehouse_navigation.png"
    resolution = 0.05
    safety_distance = 0.3
    occupancy_threshold = 127
    merge_node_distance = 0.25  # meters

    merge_threshold_px = merge_node_distance / resolution  # 5 pixels

    print("=" * 80)
    print("近接ノード分析: Python実装")
    print("=" * 80)

    # Load map
    print(f"\nマップを読み込み中: {map_path}")
    image = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        print(f"エラー: マップを読み込めませんでした: {map_path}")
        return 1

    print(f"パラメータ:")
    print(f"  merge_node_distance: {merge_node_distance}m = {merge_threshold_px:.1f}px")

    # Configure generator
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
        prune_graph=False,  # Don't prune yet
    )

    generator = WaypointGraphGenerator(config=config)

    # Build graph without pruning
    print("\nグラフ生成を開始（pruning無し）...")
    graph = generator.build_graph_from_grid_map(
        image=image,
        resolution=resolution,
        safety_distance=safety_distance,
        occupancy_threshold=occupancy_threshold,
    )

    print(f"\nStep 5後（pruning前）:")
    print(f"  ノード数: {len(graph.nodes())}")
    print(f"  エッジ数: {len(graph.edges())}")

    # Analyze close nodes before pruning
    print("\n" + "=" * 80)
    print("Step 5後の近接ノード分析:")
    print("=" * 80)
    pairs_before = analyze_close_nodes(graph, merge_threshold_px)

    # Now apply pruning manually to see what happens
    print("\n" + "=" * 80)
    print("Pruning適用中...")
    print("=" * 80)

    from swagger.waypoint_graph_generator import WaypointGraphGenerator
    import networkx as nx

    # Manually call merge function
    iteration = 0
    while True:
        iteration += 1
        print(f"\n反復 {iteration}:")

        nodes = list(graph.nodes())
        node_coords = np.array(nodes)
        tree = cKDTree(node_coords)

        # Find pairs of nodes that are close to each other
        pairs = tree.query_pairs(r=int(merge_threshold_px))

        print(f"  見つかった近接ペア: {len(pairs)}")

        if not pairs:
            print(f"  近接ペアなし、終了")
            break

        merged = False
        merge_count = 0
        skip_count = 0

        for n1_idx, n2_idx in pairs:
            n1 = nodes[n1_idx]
            n2 = nodes[n2_idx]

            # Skip if n2 has already been removed
            if not graph.has_node(n2):
                continue

            # Check collision for merging
            neighbors = [n for n in graph.neighbors(n2) if n != n1]

            if neighbors:
                collision = False
                for dst in neighbors:
                    # Simple collision check (you'd need to import from generator)
                    # For now, assume no collision
                    pass

                if not collision:
                    for neighbor in neighbors:
                        dist = np.sqrt((neighbor[0] - n1[0])**2 + (neighbor[1] - n1[1])**2)
                        graph.add_edge(n1, neighbor, weight=dist, edge_type="merge")
                    graph.remove_node(n2)
                    merged = True
                    merge_count += 1
                else:
                    skip_count += 1
            else:
                # No neighbors, safe to remove
                graph.remove_node(n2)
                merged = True
                merge_count += 1

        print(f"  統合したペア: {merge_count}")
        print(f"  スキップしたペア: {skip_count}")
        print(f"  現在のノード数: {len(graph.nodes())}")

        if not merged:
            print(f"  統合なし、終了")
            break

    print(f"\n最終結果:")
    print(f"  ノード数: {len(graph.nodes())}")
    print(f"  エッジ数: {len(graph.edges())}")
    print(f"  総反復数: {iteration}")

    # Analyze close nodes after pruning
    print("\n" + "=" * 80)
    print("Pruning後の近接ノード分析:")
    print("=" * 80)
    pairs_after = analyze_close_nodes(graph, merge_threshold_px)

    if len(pairs_after) > 0:
        print(f"\n⚠️  警告: Pruning後もまだ {len(pairs_after)} 個の近接ペアが残っています！")
        print(f"  これらのペアは統合されるべきですが、何らかの理由でスキップされました。")

    print("\n" + "=" * 80)
    print("処理完了！")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
