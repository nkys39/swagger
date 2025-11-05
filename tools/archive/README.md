# Archive Scripts

This directory contains investigation and analysis scripts that were used during development and debugging. These files are kept for reference but are not part of the main workflow.

## Files

### `analyze_skimage_algorithm.py`
Analyzes scikit-image's skeletonize algorithm in detail.
- Inspects the algorithm's parameters and behavior
- Tests different skeletonization methods

### `compare_raw_skeletons.py`
Compares raw skeleton images (before skan processing) between Python and C++.
- Compares skimage vs OpenCV skeletonization
- Analyzes topological differences (junctions, endpoints)

### `compare_skeletons.py`
General skeleton comparison tool.
- Visual comparison of skeleton outputs
- Statistical analysis of differences

### `export_skeleton_nodes.py`
Exports skeleton graph nodes from Python for C++ to use.
- Generates JSON file with node coordinates
- Includes metadata about skeleton generation

### `investigate_skan.py`
Investigates how skan processes skeleton branches.
- Analyzes skan.Skeleton class behavior
- Inspects path extraction and junction detection

### `test_compare.py`
Test script for comparing Python and C++ implementations.
- End-to-end comparison tests
- Validates graph generation pipeline

### `test_occupancy_threshold.py`
Tests different occupancy threshold values.
- Evaluates impact of threshold on graph generation
- Analyzes trade-offs

## Note

These scripts were used during the development of the C++ implementation to ensure compatibility with the Python implementation. They are archived here for historical reference and may not reflect the current state of the codebase.

For current comparison and debugging tools, see the parent `tools/` directory.
