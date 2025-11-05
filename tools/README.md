# Comparison and Visualization Tools

This directory contains tools for comparing Python and C++ implementations and visualizing results.

## Tools

### `compare_distance_transform.py`
Compare distance transform outputs from Python and C++ Step 1.

**Usage:**
```bash
python tools/compare_distance_transform.py
```

**Requirements:**
- `debug_output/python_step1_dist_transform.npy`
- `debug_output/cpp_step1_dist_transform.npy`
- `debug_output/python_step1_inflated_map.png`
- `debug_output/cpp_step1_inflated_map.png`

---

### `compare_step_by_step.py`
Compare graphs step-by-step (Steps 2-6) between Python and C++.

**Usage:**
```bash
python tools/compare_step_by_step.py
```

---

### `compare_final_graphs.py`
Compare final graph outputs from Python and C++ implementations.

**Usage:**
```bash
python tools/compare_final_graphs.py
```

---

### `create_comparison_images.py`
Generate side-by-side comparison images for all steps.

**Usage:**
```bash
python tools/create_comparison_images.py
```

**Output:**
- `comparison_step2.png`
- `comparison_step3.png`
- `comparison_step4.png`
- etc.

---

### `visualize_steps.py`
Visualize individual steps of the Python pipeline.

**Usage:**
```bash
python tools/visualize_steps.py
```

**Output:**
- `python_step2.png`
- `python_step3.png`
- etc.

---

## Workflow

1. Run Python pipeline:
   ```bash
   python scripts/run_pipeline.py --map data/maps/example.pgm --output output/python
   ```

2. Run C++ pipeline:
   ```bash
   cd swagger-cpp/build
   ./swagger_cpp --map ../../data/maps/example.pgm --output ../../output/cpp
   ```

3. Compare:
   ```bash
   python tools/compare_step_by_step.py
   python tools/create_comparison_images.py
   ```

## Debug Output

All tools expect debug output in the `debug_output/` directory (automatically created by the pipelines).
