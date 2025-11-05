#!/usr/bin/env python3
"""Analyze skimage's skeletonize algorithm in detail."""

import numpy as np
import cv2
from skimage.morphology import skeletonize
from skimage import __version__ as skimage_version

print("=" * 80)
print("skimage skeletonizeアルゴリズム詳細分析")
print("=" * 80)

print(f"\nskimageバージョン: {skimage_version}")

# Get function source info
import inspect
print(f"\nskeletonize関数の場所:")
print(f"  {inspect.getfile(skeletonize)}")

# Check available parameters
sig = inspect.signature(skeletonize)
print(f"\nパラメータ:")
for param_name, param in sig.parameters.items():
    print(f"  {param_name}: {param.default if param.default != inspect.Parameter.empty else 'required'}")

# Test with simple pattern to understand algorithm
print("\n" + "=" * 80)
print("簡単なパターンでアルゴリズムテスト")
print("=" * 80)

# Create simple test patterns
test_patterns = {
    "horizontal_line": np.zeros((10, 20), dtype=bool),
    "vertical_line": np.zeros((20, 10), dtype=bool),
    "cross": np.zeros((20, 20), dtype=bool),
    "square": np.zeros((20, 20), dtype=bool),
}

# Horizontal line
test_patterns["horizontal_line"][5, 5:15] = True

# Vertical line
test_patterns["vertical_line"][5:15, 5] = True

# Cross
test_patterns["cross"][10, 5:15] = True
test_patterns["cross"][5:15, 10] = True

# Square (filled)
test_patterns["square"][5:15, 5:15] = True

for name, pattern in test_patterns.items():
    skeleton = skeletonize(pattern)
    print(f"\n{name}:")
    print(f"  入力画素: {pattern.sum()}")
    print(f"  出力画素: {skeleton.sum()}")
    print(f"  削減率: {(1 - skeleton.sum()/pattern.sum())*100:.1f}%")

# Check if there are any parameters or preprocessing steps
print("\n" + "=" * 80)
print("前処理の確認")
print("=" * 80)

# Load actual map and test different preprocessing
map_path = "maps/carter_warehouse_navigation.png"
image = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
inflated_map = cv2.threshold(image, 127, 255, cv2.THRESH_BINARY_INV)[1]

# Test different input formats
free_map_bool = (inflated_map == 0)
free_map_uint8 = (~inflated_map).astype(np.uint8)

print(f"入力マップサイズ: {image.shape}")
print(f"自由空間画素数: {free_map_bool.sum()}")

# Test with bool input
skeleton_bool = skeletonize(free_map_bool)
print(f"\nブール入力 → スケルトン画素: {skeleton_bool.sum()}")

# Test with different method parameter if available
try:
    skeleton_zhang = skeletonize(free_map_bool, method='zhang')
    print(f"method='zhang' → スケルトン画素: {skeleton_zhang.sum()}")
except Exception as e:
    print(f"method='zhang' エラー: {e}")

try:
    skeleton_lee = skeletonize(free_map_bool, method='lee')
    print(f"method='lee' → スケルトン画素: {skeleton_lee.sum()}")
except Exception as e:
    print(f"method='lee' エラー: {e}")

# Check documentation
print("\n" + "=" * 80)
print("skeletonize関数のドキュメント:")
print("=" * 80)
print(skeletonize.__doc__)

print("\n" + "=" * 80)
print("結論:")
print("  上記の情報から、skimageがどのように前処理・アルゴリズムを")
print("  実行しているか把握し、C++実装の参考にします。")
print("=" * 80)
