#!/usr/bin/env python3
"""Compare distance transform results between Python and C++."""

import cv2
import numpy as np
import json
import os

def compare_distance_transforms():
    """Compare distance transform outputs from Python and C++."""

    # Load Python output
    py_dist_path = "debug_output/python_step1_dist_transform.npy"
    py_inflated_path = "debug_output/python_step1_inflated_map.png"

    # Load C++ output
    cpp_dist_path = "debug_output/cpp_step1_dist_transform.npy"
    cpp_inflated_path = "debug_output/cpp_step1_inflated_map.png"

    # Check if files exist
    if not os.path.exists(py_dist_path):
        print(f"❌ Python distance transform not found: {py_dist_path}")
        print("   Run Python Step 1 first to generate output")
        return

    if not os.path.exists(cpp_dist_path):
        print(f"❌ C++ distance transform not found: {cpp_dist_path}")
        print("   Run C++ Step 1 first to generate output")
        return

    # Load data
    py_dist = np.load(py_dist_path)
    py_inflated = cv2.imread(py_inflated_path, cv2.IMREAD_GRAYSCALE)

    cpp_dist = np.load(cpp_dist_path)
    cpp_inflated = cv2.imread(cpp_inflated_path, cv2.IMREAD_GRAYSCALE)

    print("=" * 70)
    print("Distance Transform Comparison")
    print("=" * 70)

    # Check shapes
    print("\n【Shape Comparison】")
    print(f"  Python distance map:  {py_dist.shape}")
    print(f"  C++ distance map:     {cpp_dist.shape}")
    print(f"  Python inflated map:  {py_inflated.shape}")
    print(f"  C++ inflated map:     {cpp_inflated.shape}")

    if py_dist.shape != cpp_dist.shape:
        print("  ⚠️  Shape mismatch!")
        return

    # Check data types
    print("\n【Data Type Comparison】")
    print(f"  Python distance dtype: {py_dist.dtype}")
    print(f"  C++ distance dtype:    {cpp_dist.dtype}")
    print(f"  Python inflated dtype: {py_inflated.dtype}")
    print(f"  C++ inflated dtype:    {cpp_inflated.dtype}")

    # Compare distance transforms
    print("\n【Distance Transform Statistics】")
    print(f"  Python - min: {py_dist.min():.6f}, max: {py_dist.max():.6f}, mean: {py_dist.mean():.6f}")
    print(f"  C++    - min: {cpp_dist.min():.6f}, max: {cpp_dist.max():.6f}, mean: {cpp_dist.mean():.6f}")

    # Check if identical
    dist_identical = np.allclose(py_dist, cpp_dist, rtol=1e-6, atol=1e-6)
    print(f"\n  Distance maps identical (tolerance=1e-6): {dist_identical}")

    if not dist_identical:
        diff = np.abs(py_dist - cpp_dist)
        max_diff = diff.max()
        mean_diff = diff.mean()
        nonzero_diff = np.count_nonzero(diff > 1e-6)

        print(f"  Maximum difference: {max_diff:.9f}")
        print(f"  Mean difference: {mean_diff:.9f}")
        print(f"  Pixels with diff > 1e-6: {nonzero_diff} / {diff.size} ({100*nonzero_diff/diff.size:.2f}%)")

        # Find location of max difference
        max_loc = np.unravel_index(diff.argmax(), diff.shape)
        print(f"  Max diff location (y, x): {max_loc}")
        print(f"    Python value: {py_dist[max_loc]:.9f}")
        print(f"    C++ value:    {cpp_dist[max_loc]:.9f}")

    # Compare inflated maps
    print("\n【Inflated Map Comparison】")
    inflated_identical = np.array_equal(py_inflated, cpp_inflated)
    print(f"  Inflated maps identical: {inflated_identical}")

    if not inflated_identical:
        py_occupied = np.count_nonzero(py_inflated > 0)
        cpp_occupied = np.count_nonzero(cpp_inflated > 0)
        print(f"  Python occupied pixels: {py_occupied}")
        print(f"  C++ occupied pixels:    {cpp_occupied}")
        print(f"  Difference:             {abs(py_occupied - cpp_occupied)}")

        # Show where they differ
        diff_mask = py_inflated != cpp_inflated
        diff_count = np.count_nonzero(diff_mask)
        print(f"  Different pixels: {diff_count} / {diff_mask.size} ({100*diff_count/diff_mask.size:.2f}%)")

        # Save difference visualization
        diff_vis = np.zeros((*py_inflated.shape, 3), dtype=np.uint8)
        diff_vis[py_inflated > cpp_inflated] = [0, 0, 255]  # Red: Python has obstacle, C++ doesn't
        diff_vis[py_inflated < cpp_inflated] = [255, 0, 0]  # Blue: C++ has obstacle, Python doesn't

        output_path = "debug_output/inflated_map_diff.png"
        cv2.imwrite(output_path, diff_vis)
        print(f"\n  Saved difference visualization: {output_path}")
        print(f"    Red:  Python has obstacle, C++ doesn't")
        print(f"    Blue: C++ has obstacle, Python doesn't")
    else:
        print("  ✅ Inflated maps are identical!")

    # Overall verdict
    print("\n" + "=" * 70)
    if dist_identical and inflated_identical:
        print("✅ RESULT: Distance transforms are IDENTICAL")
    else:
        print("⚠️  RESULT: Distance transforms DIFFER")
        if not dist_identical:
            print("   - Distance values have numerical differences")
        if not inflated_identical:
            print("   - Inflated maps differ (this affects all subsequent steps!)")
    print("=" * 70)

if __name__ == "__main__":
    compare_distance_transforms()
