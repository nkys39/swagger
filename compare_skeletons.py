#!/usr/bin/env python3
"""Compare skeleton images from C++ and Python implementations."""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

def load_and_compare_skeletons():
    """Load and visually compare skeleton images."""

    # Load images
    skeleton_python = cv2.imread("debug_output/skeleton_python.png", cv2.IMREAD_GRAYSCALE)
    skeleton_zhangsuen = cv2.imread("debug_output/skeleton_cpp_zhangsuen.png", cv2.IMREAD_GRAYSCALE)
    skeleton_guohall = cv2.imread("debug_output/skeleton_cpp_guohall.png", cv2.IMREAD_GRAYSCALE)

    if skeleton_python is None:
        print("エラー: debug_output/skeleton_python.png が見つかりません")
        print("まず Python版を実行してください: python test_compare.py")
        return

    if skeleton_zhangsuen is None:
        print("エラー: debug_output/skeleton_cpp_zhangsuen.png が見つかりません")
        print("まず C++版を実行してください")
        return

    if skeleton_guohall is None:
        print("エラー: debug_output/skeleton_cpp_guohall.png が見つかりません")
        print("まず C++版を実行してください")
        return

    # Calculate statistics
    print("=" * 80)
    print("スケルトン画像比較")
    print("=" * 80)

    python_pixels = np.count_nonzero(skeleton_python)
    zhangsuen_pixels = np.count_nonzero(skeleton_zhangsuen)
    guohall_pixels = np.count_nonzero(skeleton_guohall)

    print(f"\n画素数:")
    print(f"  Python (skimage):         {python_pixels:,} pixels")
    print(f"  C++ Zhang-Suen:           {zhangsuen_pixels:,} pixels")
    print(f"  C++ Guo-Hall:             {guohall_pixels:,} pixels")

    print(f"\nPythonとの差:")
    print(f"  Zhang-Suen vs Python:     {zhangsuen_pixels - python_pixels:+,} pixels ({((zhangsuen_pixels/python_pixels - 1) * 100):+.1f}%)")
    print(f"  Guo-Hall vs Python:       {guohall_pixels - python_pixels:+,} pixels ({((guohall_pixels/python_pixels - 1) * 100):+.1f}%)")

    # Count junctions and endpoints for each
    def count_topology(skeleton):
        """Count junctions and endpoints in a skeleton image."""
        junctions = 0
        endpoints = 0

        for y in range(1, skeleton.shape[0] - 1):
            for x in range(1, skeleton.shape[1] - 1):
                if skeleton[y, x] > 0:
                    # Count 8-connected neighbors
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

    print("\nトポロジー分析:")

    py_junc, py_end = count_topology(skeleton_python)
    print(f"  Python (skimage):")
    print(f"    分岐点: {py_junc}, 終端点: {py_end}")

    zs_junc, zs_end = count_topology(skeleton_zhangsuen)
    print(f"  C++ Zhang-Suen:")
    print(f"    分岐点: {zs_junc}, 終端点: {zs_end}")

    gh_junc, gh_end = count_topology(skeleton_guohall)
    print(f"  C++ Guo-Hall:")
    print(f"    分岐点: {gh_junc}, 終端点: {gh_end}")

    # Calculate difference images
    diff_zhangsuen = cv2.absdiff(skeleton_python, skeleton_zhangsuen)
    diff_guohall = cv2.absdiff(skeleton_python, skeleton_guohall)

    diff_zs_pixels = np.count_nonzero(diff_zhangsuen)
    diff_gh_pixels = np.count_nonzero(diff_guohall)

    print(f"\n画像差分 (異なる画素数):")
    print(f"  Zhang-Suen vs Python:     {diff_zs_pixels:,} pixels")
    print(f"  Guo-Hall vs Python:       {diff_gh_pixels:,} pixels")

    # Create comparison visualization
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('スケルトン画像比較', fontsize=16, fontweight='bold')

    # Row 1: Original skeletons
    axes[0, 0].imshow(skeleton_python, cmap='gray')
    axes[0, 0].set_title(f'Python (skimage)\n{python_pixels} pixels, {py_junc} junctions')
    axes[0, 0].axis('off')

    axes[0, 1].imshow(skeleton_zhangsuen, cmap='gray')
    axes[0, 1].set_title(f'C++ Zhang-Suen\n{zhangsuen_pixels} pixels, {zs_junc} junctions')
    axes[0, 1].axis('off')

    axes[0, 2].imshow(skeleton_guohall, cmap='gray')
    axes[0, 2].set_title(f'C++ Guo-Hall\n{guohall_pixels} pixels, {gh_junc} junctions')
    axes[0, 2].axis('off')

    # Row 2: Difference images
    axes[1, 0].imshow(skeleton_python, cmap='gray')
    axes[1, 0].set_title('Python (参照)')
    axes[1, 0].axis('off')

    axes[1, 1].imshow(diff_zhangsuen, cmap='hot')
    axes[1, 1].set_title(f'差分: Zhang-Suen vs Python\n{diff_zs_pixels} different pixels')
    axes[1, 1].axis('off')

    axes[1, 2].imshow(diff_guohall, cmap='hot')
    axes[1, 2].set_title(f'差分: Guo-Hall vs Python\n{diff_gh_pixels} different pixels')
    axes[1, 2].axis('off')

    plt.tight_layout()

    # Save comparison
    output_path = "debug_output/skeleton_comparison.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n比較画像を保存しました: {output_path}")

    # Show plot
    plt.show()

    # Recommendation
    print("\n" + "=" * 80)
    print("推奨:")
    if diff_gh_pixels < diff_zs_pixels:
        print(f"  ✓ Guo-Hall法がPythonに近いです (差分: {diff_gh_pixels} pixels)")
    else:
        print(f"  ✓ Zhang-Suen法がPythonに近いです (差分: {diff_zs_pixels} pixels)")

    if gh_junc == py_junc:
        print(f"  ✓ Guo-Hall法の分岐点数がPythonと一致しています！")
    elif zs_junc == py_junc:
        print(f"  ✓ Zhang-Suen法の分岐点数がPythonと一致しています！")
    else:
        print(f"  ⚠ どちらの方法も分岐点数が一致しません")
        print(f"    → skimageのアルゴリズムをC++に移植する必要があるかもしれません")

    print("=" * 80)

if __name__ == "__main__":
    load_and_compare_skeletons()
