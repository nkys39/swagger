#!/usr/bin/env python3
"""Create side-by-side comparison images of C++ and Python implementations."""

import sys
import numpy as np
import cv2
from pathlib import Path


def create_side_by_side_comparison(python_dir, cpp_dir, output_dir):
    """Create side-by-side comparison images for each step."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    python_path = Path(python_dir)
    cpp_path = Path(cpp_dir)

    steps = [
        ("step2", "Step 2: Skeleton"),
        ("step3", "Step 3: + Boundary"),
        ("step4", "Step 4: + Free Space"),
        ("step5", "Step 5: + Delaunay"),
        ("step6", "Step 6: + Pruning"),
    ]

    print("\n" + "=" * 80)
    print("Creating Side-by-Side Comparisons")
    print("=" * 80)

    comparison_images = []

    for step_name, title in steps:
        python_file = python_path / f"python_{step_name}.png"
        cpp_file = cpp_path / f"cpp_{step_name}.png"

        if not python_file.exists():
            print(f"Warning: {python_file} not found, skipping {step_name}")
            continue

        if not cpp_file.exists():
            print(f"Warning: {cpp_file} not found, skipping {step_name}")
            continue

        # Load images
        python_img = cv2.imread(str(python_file))
        cpp_img = cv2.imread(str(cpp_file))

        if python_img is None or cpp_img is None:
            print(f"Error loading images for {step_name}")
            continue

        # Ensure same height
        h_py, w_py = python_img.shape[:2]
        h_cpp, w_cpp = cpp_img.shape[:2]

        if h_py != h_cpp:
            # Resize to match heights
            if h_py > h_cpp:
                cpp_img = cv2.resize(cpp_img, (int(w_cpp * h_py / h_cpp), h_py))
            else:
                python_img = cv2.resize(python_img, (int(w_py * h_cpp / h_py), h_cpp))

        # Create side-by-side
        comparison = np.hstack([python_img, cpp_img])

        # Add title
        h, w = comparison.shape[:2]
        header_height = 80
        header = np.zeros((header_height, w, 3), dtype=np.uint8)

        # Add title text
        cv2.putText(header, title, (w//2 - 200, 50), cv2.FONT_HERSHEY_SIMPLEX,
                    1.5, (255, 255, 255), 3, cv2.LINE_AA)

        # Add labels for Python and C++
        cv2.putText(header, "Python", (w//4 - 50, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(header, "C++", (3*w//4 - 30, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2, cv2.LINE_AA)

        # Combine header and comparison
        final_img = np.vstack([header, comparison])

        # Save individual comparison
        output_file = output_path / f"comparison_{step_name}.png"
        cv2.imwrite(str(output_file), final_img)
        print(f"Created: {output_file}")

        # Store for grid
        comparison_images.append(final_img)

    # Create vertical grid of all comparisons
    if comparison_images:
        # Resize all to same width
        max_width = max(img.shape[1] for img in comparison_images)
        resized_images = []
        for img in comparison_images:
            if img.shape[1] < max_width:
                # Pad to max width
                pad_width = max_width - img.shape[1]
                img = np.pad(img, ((0, 0), (0, pad_width), (0, 0)), mode='constant')
            resized_images.append(img)

        grid = np.vstack(resized_images)
        grid_file = output_path / "comparison_all_steps.png"
        cv2.imwrite(str(grid_file), grid)
        print(f"\nCreated full comparison grid: {grid_file}")

    print("\n" + "=" * 80)
    print("Comparison Images Complete!")
    print("=" * 80)


def main():
    python_dir = "visualization_output"
    cpp_dir = "output"
    output_dir = "comparison_output"

    print("=" * 80)
    print("Side-by-Side Comparison Generator")
    print("=" * 80)
    print(f"\nInput directories:")
    print(f"  Python: {python_dir}")
    print(f"  C++: {cpp_dir}")
    print(f"  Output: {output_dir}")

    create_side_by_side_comparison(python_dir, cpp_dir, output_dir)

    print(f"\nGenerated files in '{output_dir}/':")
    print("  - comparison_step2.png  (Python vs C++ - Skeleton)")
    print("  - comparison_step3.png  (Python vs C++ - + Boundary)")
    print("  - comparison_step4.png  (Python vs C++ - + Free Space)")
    print("  - comparison_step5.png  (Python vs C++ - + Delaunay)")
    print("  - comparison_step6.png  (Python vs C++ - + Pruning)")
    print("  - comparison_all_steps.png  (All steps in one image)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
