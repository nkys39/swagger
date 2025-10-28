#!/usr/bin/env python3
"""Test script to verify occupancy_threshold parameter works correctly."""

import numpy as np
import cv2
from swagger import WaypointGraphGenerator

# Create a simple test map (100x100 pixels)
test_map = np.zeros((100, 100), dtype=np.uint8)

# Create different regions with different grayscale values
# Top-left: black (0) - definitely occupied
test_map[0:50, 0:50] = 0

# Top-right: dark gray (100) - ambiguous
test_map[0:50, 50:100] = 100

# Bottom-left: light gray (150) - ambiguous
test_map[50:100, 0:50] = 150

# Bottom-right: white (255) - definitely free
test_map[50:100, 50:100] = 255

print("Test map created with 4 regions:")
print("  Top-left (0-49, 0-49): value=0 (black)")
print("  Top-right (0-49, 50-99): value=100 (dark gray)")
print("  Bottom-left (50-99, 0-49): value=150 (light gray)")
print("  Bottom-right (50-99, 50-99): value=255 (white)")
print()

# Test with different thresholds
thresholds = [50, 100, 127, 150, 200]

for threshold in thresholds:
    print(f"\n{'='*60}")
    print(f"Testing with occupancy_threshold={threshold}")
    print(f"{'='*60}")

    generator = WaypointGraphGenerator()

    try:
        graph = generator.build_graph_from_grid_map(
            image=test_map,
            resolution=0.1,
            safety_distance=0.3,
            occupancy_threshold=threshold
        )

        print(f"✅ Graph generated successfully")
        print(f"   Nodes: {len(graph.nodes())}")
        print(f"   Edges: {len(graph.edges())}")

        # Calculate expected free space
        free_pixels = np.sum(test_map > threshold)
        total_pixels = test_map.size
        expected_free_pct = (free_pixels / total_pixels) * 100

        print(f"   Expected free space: {free_pixels}/{total_pixels} pixels ({expected_free_pct:.1f}%)")

        # Show which regions should be free
        regions_free = []
        if 0 > threshold:
            regions_free.append("Top-left(0)")
        if 100 > threshold:
            regions_free.append("Top-right(100)")
        if 150 > threshold:
            regions_free.append("Bottom-left(150)")
        if 255 > threshold:
            regions_free.append("Bottom-right(255)")

        print(f"   Regions considered FREE: {', '.join(regions_free) if regions_free else 'NONE'}")

    except Exception as e:
        print(f"❌ Error: {e}")

print(f"\n{'='*60}")
print("Test completed!")
print(f"{'='*60}")
print("\nExpected behavior:")
print("  threshold=50:  3 regions free (100, 150, 255)")
print("  threshold=100: 2 regions free (150, 255)")
print("  threshold=127: 2 regions free (150, 255)")
print("  threshold=150: 1 region free (255)")
print("  threshold=200: 1 region free (255)")
