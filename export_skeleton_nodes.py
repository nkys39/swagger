#!/usr/bin/env python3
"""Export skeleton nodes from Python for C++ to use."""

import numpy as np
import cv2
from skimage.morphology import skeletonize
import skan
import json

def export_skeleton_nodes():
    """Export skeleton graph nodes that match Python's skan processing."""

    # Load and process map (same as WaypointGraphGenerator)
    map_path = "maps/carter_warehouse_navigation.png"
    image = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)

    resolution = 0.05  # m/px
    safety_distance = 0.3  # m
    occupancy_threshold = 127
    skeleton_sample_distance = 1.5  # m

    # Inflate map
    kernel_size = int(safety_distance / resolution)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size * 2 + 1, kernel_size * 2 + 1))
    inflated_map = cv2.threshold(image, occupancy_threshold, 255, cv2.THRESH_BINARY_INV)[1]
    inflated_map = cv2.dilate(inflated_map, kernel)

    # Compute skeleton
    free_map = inflated_map == 0
    skeleton_image = skeletonize(free_map)

    # Process with skan
    skeleton = skan.Skeleton(skeleton_image)
    skeleton_sample_distance_px = int(skeleton_sample_distance / resolution)

    # Build node list (matching Python's implementation)
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
