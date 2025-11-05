#!/usr/bin/env python3
"""Investigate how skan processes skeleton branches."""

import numpy as np
import cv2
from skimage.morphology import skeletonize
import skan

# Load map
map_path = "maps/carter_warehouse_navigation.png"
image = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
inflated_map = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY_INV)[1]

# Compute skeleton
print("=" * 80)
print("skan分岐処理の調査")
print("=" * 80)

skeleton_image = skeletonize(1 - (inflated_map > 0))

# Count raw junctions before skan
skeleton_uint8 = (skeleton_image * 255).astype(np.uint8)
raw_junctions = 0
raw_endpoints = 0

for y in range(1, skeleton_uint8.shape[0] - 1):
    for x in range(1, skeleton_uint8.shape[1] - 1):
        if skeleton_uint8[y, x] > 0:
            neighbors = 0
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dy == 0 and dx == 0:
                        continue
                    if skeleton_uint8[y + dy, x + dx] > 0:
                        neighbors += 1
            if neighbors >= 3:
                raw_junctions += 1
            elif neighbors == 1:
                raw_endpoints += 1

print(f"\n【生のスケルトン（skeletonize直後）】")
print(f"  画素数: {skeleton_image.sum()}")
print(f"  分岐点: {raw_junctions}")
print(f"  終端点: {raw_endpoints}")

# Process with skan
skeleton = skan.Skeleton(skeleton_image)

print(f"\n【skan.Skeleton処理後】")
print(f"  パス数: {skeleton.n_paths}")
print(f"  総エッジ数: {len(skeleton.coordinates)}")

# Analyze skan's path structure
print(f"\n【skanパスの詳細】")
path_lengths = []
for i in range(skeleton.n_paths):
    coords = skeleton.path_coordinates(i)
    path_lengths.append(len(coords))

print(f"  平均パス長: {np.mean(path_lengths):.1f} pixels")
print(f"  最小パス長: {min(path_lengths)} pixels")
print(f"  最大パス長: {max(path_lengths)} pixels")

# Check if skan has junction information
print(f"\n【skanの属性】")
if hasattr(skeleton, 'junction_labels'):
    print(f"  junction_labels: {skeleton.junction_labels}")
if hasattr(skeleton, 'n_junctions'):
    print(f"  n_junctions: {skeleton.n_junctions}")
if hasattr(skeleton, 'degrees'):
    print(f"  degrees: {skeleton.degrees}")
    unique_degrees, counts = np.unique(skeleton.degrees, return_counts=True)
    print(f"  次数の分布:")
    for deg, count in zip(unique_degrees, counts):
        print(f"    次数 {deg}: {count} ノード")

# Check skeleton.paths
print(f"\n【skan.paths_table()】")
try:
    paths_df = skan.summarize(skeleton)
    print(paths_df.head(10))
    print(f"\n  総パス数: {len(paths_df)}")
except Exception as e:
    print(f"  エラー: {e}")

print("\n" + "=" * 80)
print("結論:")
print("  skanは生のスケルトンから分岐を統合・簡略化して、")
print("  より少ないパス数を生成しています。")
print("  C++でも同様の統合処理が必要です。")
print("=" * 80)
