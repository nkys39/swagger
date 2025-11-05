#!/usr/bin/env python3
"""Compare raw skeleton images (before skan processing)."""

import numpy as np
import cv2
from skimage.morphology import skeletonize

# Load map
map_path = "maps/carter_warehouse_navigation.png"
image = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)

# Create inflated map (same as C++)
inflated_map = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY_INV)[1]
free_map = ~inflated_map

# Compute skeleton using skimage (what Python uses)
print("=" * 80)
print("生のスケルトン比較（skan処理前）")
print("=" * 80)

skeleton_skimage = skeletonize(free_map > 0)
skeleton_skimage_uint8 = (skeleton_skimage * 255).astype(np.uint8)

# Save for comparison
cv2.imwrite("debug_output/skeleton_python_raw.png", skeleton_skimage_uint8)

# Compute skeleton using OpenCV Zhang-Suen (what C++ uses)
binary = cv2.threshold(free_map, 127, 255, cv2.THRESH_BINARY)[1]
skeleton_opencv_zs = cv2.ximgproc.thinning(binary, thinningType=cv2.ximgproc.THINNING_ZHANGSUEN)
cv2.imwrite("debug_output/skeleton_opencv_zhangsuen.png", skeleton_opencv_zs)

# Compute using Guo-Hall
skeleton_opencv_gh = cv2.ximgproc.thinning(binary, thinningType=cv2.ximgproc.THINNING_GUOHALL)
cv2.imwrite("debug_output/skeleton_opencv_guohall.png", skeleton_opencv_gh)

# Count topology for each
def count_topology(skeleton):
    """Count junctions and endpoints."""
    junctions = 0
    endpoints = 0

    for y in range(1, skeleton.shape[0] - 1):
        for x in range(1, skeleton.shape[1] - 1):
            if skeleton[y, x] > 0:
                neighbors = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue
                        if skeleton[y + dy, x + dx] > 0:
                            neighbors += 1
                if neighbors >= 3:
                    junctions += 1
                elif neighbors == 1:
                    endpoints += 1

    return junctions, endpoints

print("\n【skimage.morphology.skeletonize (Pythonが使用)】")
sk_pixels = np.count_nonzero(skeleton_skimage_uint8)
sk_junc, sk_end = count_topology(skeleton_skimage_uint8)
print(f"  画素数: {sk_pixels}")
print(f"  分岐点: {sk_junc}")
print(f"  終端点: {sk_end}")

print("\n【OpenCV Zhang-Suen (C++が使用していた)】")
zs_pixels = np.count_nonzero(skeleton_opencv_zs)
zs_junc, zs_end = count_topology(skeleton_opencv_zs)
print(f"  画素数: {zs_pixels}")
print(f"  分岐点: {zs_junc}")
print(f"  終端点: {zs_end}")

print("\n【OpenCV Guo-Hall (C++が今使用)】")
gh_pixels = np.count_nonzero(skeleton_opencv_gh)
gh_junc, gh_end = count_topology(skeleton_opencv_gh)
print(f"  画素数: {gh_pixels}")
print(f"  分岐点: {gh_junc}")
print(f"  終端点: {gh_end}")

# Compute differences
diff_zs = cv2.absdiff(skeleton_skimage_uint8, skeleton_opencv_zs)
diff_gh = cv2.absdiff(skeleton_skimage_uint8, skeleton_opencv_gh)

print("\n【差分（skimage vs OpenCV）】")
print(f"  Zhang-Suen: {np.count_nonzero(diff_zs)} different pixels")
print(f"  Guo-Hall:   {np.count_nonzero(diff_gh)} different pixels")

print("\n" + "=" * 80)
print("結論:")
if abs(sk_junc - zs_junc) < 10:
    print("  ✓ skimageとOpenCV Zhang-Suenの分岐点数はほぼ同じ")
    print("  → 問題はskan.Skeletonの処理にある")
    print("  → C++でもskanと同様の分岐統合処理を実装する必要がある")
elif abs(sk_junc - gh_junc) < 10:
    print("  ✓ skimageとOpenCV Guo-Hallの分岐点数はほぼ同じ")
    print("  → Guo-Hallを使用し、skanと同様の処理を実装する")
else:
    print("  ✗ どのOpenCVメソッドもskimageと一致しない")
    print(f"  → skimageの実装をC++に移植する必要がある")
    print(f"     skimage分岐点: {sk_junc}")
    print(f"     Zhang-Suen分岐点: {zs_junc}")
    print(f"     Guo-Hall分岐点: {gh_junc}")
print("=" * 80)
