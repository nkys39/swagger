#!/usr/bin/env python3
"""Analyze the difference between Python and C++ inflated maps."""

import cv2
import numpy as np

# Load the inflated maps
py_inflated = cv2.imread("debug_output/python_step1_inflated_map.png", cv2.IMREAD_GRAYSCALE)
cpp_inflated = cv2.imread("debug_output/cpp_step1_inflated_map.png", cv2.IMREAD_GRAYSCALE)

print("=== Inflated Map Value Analysis ===")
print(f"\nPython inflated map:")
print(f"  Unique values: {np.unique(py_inflated)}")
print(f"  Min: {py_inflated.min()}, Max: {py_inflated.max()}")
print(f"  Values > 0: {np.count_nonzero(py_inflated > 0)}")
print(f"  Values == 255: {np.count_nonzero(py_inflated == 255)}")
print(f"  Values == 1: {np.count_nonzero(py_inflated == 1)}")

print(f"\nC++ inflated map:")
print(f"  Unique values: {np.unique(cpp_inflated)}")
print(f"  Min: {cpp_inflated.min()}, Max: {cpp_inflated.max()}")
print(f"  Values > 0: {np.count_nonzero(cpp_inflated > 0)}")
print(f"  Values == 255: {np.count_nonzero(cpp_inflated == 255)}")
print(f"  Values == 1: {np.count_nonzero(cpp_inflated == 1)}")

# Check if values are different
print(f"\n=== Difference Pattern ===")
print(f"Python > 0 and C++ == 0: {np.count_nonzero((py_inflated > 0) & (cpp_inflated == 0))}")
print(f"Python == 0 and C++ > 0: {np.count_nonzero((py_inflated == 0) & (cpp_inflated > 0))}")
print(f"Both > 0 but different values: {np.count_nonzero((py_inflated > 0) & (cpp_inflated > 0) & (py_inflated != cpp_inflated))}")

# Sample some specific locations
print(f"\n=== Sample Values ===")
print(f"Location (100, 100):")
print(f"  Python: {py_inflated[100, 100]}")
print(f"  C++:    {cpp_inflated[100, 100]}")

print(f"Location (200, 200):")
print(f"  Python: {py_inflated[200, 200]}")
print(f"  C++:    {cpp_inflated[200, 200]}")

# Check if the issue is value interpretation (0/1 vs 0/255)
if cpp_inflated.max() == 1:
    print("\n⚠️  C++ inflated map uses 0/1 instead of 0/255!")
    print("   Converting C++ to 0/255 for comparison...")
    cpp_inflated_fixed = (cpp_inflated * 255).astype(np.uint8)
    if np.array_equal(py_inflated, cpp_inflated_fixed):
        print("   ✅ After conversion, maps are IDENTICAL!")
    else:
        print("   ❌ Even after conversion, maps differ")
elif py_inflated.max() == 1:
    print("\n⚠️  Python inflated map uses 0/1 instead of 0/255!")
