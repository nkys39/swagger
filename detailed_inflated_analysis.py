#!/usr/bin/env python3
"""Detailed analysis of inflated map differences."""

import cv2
import numpy as np

# Load maps
py_inflated = cv2.imread("debug_output/python_step1_inflated_map.png", cv2.IMREAD_GRAYSCALE)
cpp_inflated = cv2.imread("debug_output/cpp_step1_inflated_map.png", cv2.IMREAD_GRAYSCALE)
py_dist = np.load("debug_output/python_step1_dist_transform.npy")
cpp_dist = np.load("debug_output/cpp_step1_dist_transform.npy")

print("=== DETAILED VALUE ANALYSIS ===\n")

# Check unique values
print("Python inflated unique values:", np.unique(py_inflated))
print("C++ inflated unique values:", np.unique(cpp_inflated))

# Sample some specific pixels
print("\n=== SAMPLE PIXEL COMPARISON ===")
for y, x in [(100, 100), (200, 200), (300, 300), (400, 400)]:
    print(f"\nPixel ({y}, {x}):")
    print(f"  Python: dist={py_dist[y,x]:.6f}, inflated={py_inflated[y,x]}")
    print(f"  C++:    dist={cpp_dist[y,x]:.6f}, inflated={cpp_inflated[y,x]}")
    print(f"  Match: {py_inflated[y,x] == cpp_inflated[y,x]}")

# Find where they differ
print("\n=== DIFFERENCE LOCATIONS ===")
diff_mask = py_inflated != cpp_inflated
y_coords, x_coords = np.where(diff_mask)

if len(y_coords) > 0:
    # Sample 10 different locations
    sample_indices = np.linspace(0, len(y_coords)-1, min(10, len(y_coords)), dtype=int)

    print(f"\nSampling {len(sample_indices)} locations where maps differ:")
    for idx in sample_indices:
        y, x = y_coords[idx], x_coords[idx]
        print(f"\n  Location ({y}, {x}):")
        print(f"    Python: dist={py_dist[y,x]:.6f}, inflated={py_inflated[y,x]}")
        print(f"    C++:    dist={cpp_dist[y,x]:.6f}, inflated={cpp_inflated[y,x]}")

# Check if it's an inversion
print("\n=== INVERSION CHECK ===")
inverted = (py_inflated == 0) == (cpp_inflated == 255)
inverted_count = np.count_nonzero(inverted)
total = py_inflated.size
print(f"Pixels that match if inverted: {inverted_count} / {total} ({100*inverted_count/total:.2f}%)")

# Check correlation
print("\n=== CORRELATION ===")
correlation = np.corrcoef(py_inflated.flatten(), cpp_inflated.flatten())[0, 1]
print(f"Correlation coefficient: {correlation:.6f}")
if correlation < -0.9:
    print("  ⚠️  Strong NEGATIVE correlation - maps are likely inverted!")
elif correlation > 0.9:
    print("  ✅ Strong positive correlation")

# Try binary threshold on both
print("\n=== BINARY THRESHOLD CHECK ===")
py_binary = (py_inflated > 0).astype(np.uint8) * 255
cpp_binary = (cpp_inflated > 0).astype(np.uint8) * 255
binary_match = np.array_equal(py_binary, cpp_binary)
print(f"After binary threshold (>0), maps match: {binary_match}")

if not binary_match:
    # Check if binary maps are inverted
    cpp_inverted = (cpp_inflated == 0).astype(np.uint8) * 255
    inverted_match = np.array_equal(py_binary, cpp_inverted)
    print(f"Python matches INVERTED C++: {inverted_match}")
