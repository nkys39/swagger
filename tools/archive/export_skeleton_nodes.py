#!/usr/bin/env python3
"""Export skeleton nodes from Python for C++ to use."""

import numpy as np
import cv2
from skimage.morphology import skeletonize
import skan
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def export_skeleton_nodes():
    """Export skeleton graph nodes that match Python's skan processing."""

    # Load and process map (same as WaypointGraphGenerator)
    map_path = "maps/carter_warehouse_navigation.png"

    print("=" * 80)
    print("Pythonスケルトンノードのエクスポート")
    print("=" * 80)

    image = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        print(f"エラー: マップを読み込めませんでした: {map_path}")
        return None

    resolution = 0.05  # m/px
    safety_distance = 0.3  # m
    occupancy_threshold = 127
    skeleton_sample_distance = 1.5  # m

    print(f"\nパラメータ:")
    print(f"  マップ: {map_path}")
    print(f"  解像度: {resolution} m/px")
    print(f"  安全距離: {safety_distance} m")
    print(f"  スケルトンサンプル距離: {skeleton_sample_distance} m")

    # Inflate map
    kernel_size = int(safety_distance / resolution)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size * 2 + 1, kernel_size * 2 + 1))
    inflated_map = cv2.threshold(image, occupancy_threshold, 255, cv2.THRESH_BINARY_INV)[1]
    inflated_map = cv2.dilate(inflated_map, kernel)

    print(f"\n膨張処理:")
    print(f"  カーネルサイズ: {kernel_size}")
    print(f"  膨張後の障害物画素: {np.count_nonzero(inflated_map)}")

    # Compute skeleton
    free_map = inflated_map == 0
    print(f"\nスケルトン化:")
    print(f"  自由空間画素: {np.count_nonzero(free_map)}")

    skeleton_image = skeletonize(free_map)
    skeleton_pixels = np.count_nonzero(skeleton_image)
    print(f"  スケルトン画素: {skeleton_pixels}")

    # Process with skan
    print(f"\nskan処理:")
    skeleton = skan.Skeleton(skeleton_image)
    print(f"  skanパス数: {skeleton.n_paths}")

    skeleton_sample_distance_px = int(skeleton_sample_distance / resolution)
    print(f"  サンプル距離: {skeleton_sample_distance_px} px")

    # Build node list (matching Python's implementation)
    print(f"\nノード生成中...")
    nodes = []
    edges = []

    for i in range(skeleton.n_paths):
        branch = skeleton.path_coordinates(i)
        num_segments = max(1, len(branch) // skeleton_sample_distance_px)
        segment_length = len(branch) // num_segments

        for j in range(num_segments):
            start_idx = j * segment_length
            end_idx = min((j + 1) * segment_length, len(branch) - 1)

            start = branch[start_idx]
            end = branch[end_idx]

            # Store as (row, col) to match C++ NodeId
            node_start = [int(start[0]), int(start[1])]
            node_end = [int(end[0]), int(end[1])]

            if node_start not in nodes:
                nodes.append(node_start)
            if node_end not in nodes:
                nodes.append(node_end)

            # Store edge
            edges.append({
                "start": node_start,
                "end": node_end,
                "type": "skeleton"
            })

    # Export to JSON
    output = {
        "resolution": resolution,
        "skeleton_sample_distance": skeleton_sample_distance,
        "nodes": nodes,
        "edges": edges,
        "statistics": {
            "num_nodes": len(nodes),
            "num_edges": len(edges),
            "num_skan_paths": skeleton.n_paths
        }
    }

    with open("skeleton_nodes.json", "w") as f:
        json.dump(output, f, indent=2)

    print("=" * 80)
    print("スケルトンノードエクスポート完了")
    print("=" * 80)
    print(f"ノード数: {len(nodes)}")
    print(f"エッジ数: {len(edges)}")
    print(f"skanパス数: {skeleton.n_paths}")
    print(f"\n出力ファイル: skeleton_nodes.json")
    print("=" * 80)

    return output

if __name__ == "__main__":
    export_skeleton_nodes()
