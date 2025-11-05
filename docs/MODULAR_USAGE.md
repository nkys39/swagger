# モジュラー実行ガイド / Modular Execution Guide

[English](#english) | [日本語](#japanese)

---

## <a name="japanese"></a>日本語

このガイドでは、SWAGGER グラフ生成アルゴリズムの各ステップを個別に実行する方法を説明します。

### 概要

グラフ生成処理は以下の6つのステップに分割されています：

1. **前処理** (`step1_preprocess.py`) - 距離変換と障害物膨張
2. **スケルトングラフ** (`step2_skeleton_graph.py`) - 中央軸からのグラフ生成
3. **境界サンプリング** (`step3_boundary_sampling.py`) - 障害物境界のノード追加
4. **自由空間サンプリング** (`step4_free_space_sampling.py`) - 広い空間のノード追加
5. **Delaunayショートカット** (`step5_delaunay_shortcuts.py`) - 三角分割による近道追加
6. **グラフ剪定** (`step6_prune_graph.py`) - 不要なノード・エッジの削除と最適化

### ディレクトリ構造

```
scripts/
├── steps/                          # 個別ステップスクリプト
│   ├── __init__.py
│   ├── common.py                   # 共通ユーティリティ
│   ├── step1_preprocess.py         # ステップ1: 前処理
│   ├── step2_skeleton_graph.py     # ステップ2: スケルトン
│   ├── step3_boundary_sampling.py  # ステップ3: 境界
│   ├── step4_free_space_sampling.py # ステップ4: 自由空間
│   ├── step5_delaunay_shortcuts.py # ステップ5: ショートカット
│   └── step6_prune_graph.py        # ステップ6: 剪定
└── run_pipeline.py                 # パイプライン実行スクリプト
```

## 使い方

### 方法1: パイプライン全体を実行

すべてのステップを一度に実行：

```bash
python scripts/run_pipeline.py \
  --map data/map.png \
  --output output/ \
  --resolution 0.05 \
  --safety-distance 0.5
```

### 方法2: 特定のステップのみ実行

```bash
# ステップ1, 2, 5のみ実行
python scripts/run_pipeline.py \
  --map data/map.png \
  --output output/ \
  --steps 1,2,5
```

### 方法3: 一部のステップをスキップ

```bash
# ステップ3と4をスキップ
python scripts/run_pipeline.py \
  --map data/map.png \
  --output output/ \
  --skip-steps 3,4
```

### 方法4: 各ステップを手動で実行

完全な制御が必要な場合：

```bash
# ステップ1: 前処理
python scripts/steps/step1_preprocess.py \
  --map data/map.png \
  --output output/ \
  --resolution 0.05 \
  --safety-distance 0.5

# ステップ2: スケルトングラフ
python scripts/steps/step2_skeleton_graph.py \
  --input output/ \
  --output output/ \
  --skeleton-sample-distance 1.5 \
  --visualize

# ステップ3: 境界サンプリング
python scripts/steps/step3_boundary_sampling.py \
  --input output/ \
  --output output/ \
  --boundary-inflation-factor 1.5 \
  --boundary-sample-distance 2.5 \
  --visualize

# ステップ4: 自由空間サンプリング
python scripts/steps/step4_free_space_sampling.py \
  --input output/ \
  --output output/ \
  --free-space-sampling-threshold 1.5 \
  --visualize

# ステップ5: Delaunayショートカット
python scripts/steps/step5_delaunay_shortcuts.py \
  --input output/ \
  --output output/ \
  --visualize

# ステップ6: グラフ剪定
python scripts/steps/step6_prune_graph.py \
  --input output/ \
  --output output/ \
  --merge-node-distance 0.25 \
  --min-subgraph-length 0.25 \
  --visualize \
  --output-graph final_graph.pkl
```

## パラメータ詳細

### ステップ1: 前処理
- `--map`: 占有グリッド地図のパス（必須）
- `--resolution`: 地図解像度（メートル/ピクセル）、デフォルト: 0.05
- `--safety-distance`: ロボット半径（メートル）、デフォルト: 0.5
- `--occupancy-threshold`: 占有閾値（0-255）、デフォルト: 127

### ステップ2: スケルトングラフ
- `--skeleton-sample-distance`: スケルトン上のサンプリング間隔（メートル）、デフォルト: 1.5
- `--visualize`: グラフの可視化を保存

### ステップ3: 境界サンプリング
- `--boundary-inflation-factor`: 境界膨張係数、デフォルト: 1.5
- `--boundary-sample-distance`: 境界上のサンプリング間隔（メートル）、デフォルト: 2.5
- `--visualize`: グラフの可視化を保存

### ステップ4: 自由空間サンプリング
- `--free-space-sampling-threshold`: 自由空間検出の閾値（メートル）、デフォルト: 1.5
- `--visualize`: グラフの可視化を保存

### ステップ5: Delaunayショートカット
- `--visualize`: グラフの可視化を保存

### ステップ6: グラフ剪定
- `--merge-node-distance`: ノードをマージする最大距離（メートル）、デフォルト: 0.25
- `--min-subgraph-length`: 保持する最小サブグラフ長（メートル）、デフォルト: 0.25
- `--output-graph`: 最終グラフのファイル名、デフォルト: final_graph.pkl
- `--visualize`: グラフの可視化を保存

## 実用例

### 例1: デバッグ用に各ステップを可視化

```bash
python scripts/run_pipeline.py \
  --map data/map.png \
  --output debug_output/ \
  --visualize-all \
  --log-level DEBUG
```

これにより、各ステップの出力画像が `debug_output/` に保存されます：
- `step2_skeleton_graph.png` - スケルトングラフ
- `step3_boundary_sampling.png` - 境界ノード追加後
- `step4_free_space_sampling.png` - 自由空間ノード追加後
- `step5_delaunay_shortcuts.png` - ショートカット追加後
- `step6_final_graph.png` - 最終グラフ

### 例2: スケルトンと境界のみを使用

```bash
python scripts/run_pipeline.py \
  --map data/map.png \
  --output output/ \
  --steps 1,2,3,6
```

### 例3: カスタムパラメータで実験

```bash
# 密なグラフを生成
python scripts/run_pipeline.py \
  --map data/map.png \
  --output dense_graph/ \
  --skeleton-sample-distance 0.5 \
  --boundary-sample-distance 1.0 \
  --free-space-sampling-threshold 1.0

# 疎なグラフを生成
python scripts/run_pipeline.py \
  --map data/map.png \
  --output sparse_graph/ \
  --skeleton-sample-distance 3.0 \
  --boundary-sample-distance 5.0 \
  --free-space-sampling-threshold 3.0
```

### 例4: ステップ2の結果を確認してから続行

```bash
# まずステップ1-2を実行して結果を確認
python scripts/run_pipeline.py \
  --map data/map.png \
  --output output/ \
  --steps 1,2 \
  --visualize-all

# 結果を確認後、残りのステップを実行
python scripts/run_pipeline.py \
  --map data/map.png \
  --output output/ \
  --steps 3,4,5,6
```

## 中間データ

各ステップは中間データを `<output_dir>/stepN_data.pkl` として保存します：
- `step1_data.pkl` - 前処理済み地図と距離変換
- `step2_data.pkl` - スケルトングラフ
- `step3_data.pkl` - 境界ノード追加後のグラフ
- `step4_data.pkl` - 自由空間ノード追加後のグラフ
- `step5_data.pkl` - ショートカット追加後のグラフ

最終的なグラフは `final_graph.pkl` として保存され、NetworkXグラフオブジェクトとして読み込めます。

## トラブルシューティング

### ステップが失敗する場合

```bash
# より詳細なログでステップを個別に実行
python scripts/steps/step2_skeleton_graph.py \
  --input output/ \
  --output output/ \
  --log-level DEBUG
```

### 中間データを確認

```python
import pickle
import networkx as nx

# ステップ2のデータを読み込み
with open('output/step2_data.pkl', 'rb') as f:
    data = pickle.load(f)

print(f"Nodes: {len(data.graph.nodes)}")
print(f"Edges: {len(data.graph.edges)}")
```

---

## <a name="english"></a>English

This guide explains how to run each step of the SWAGGER graph generation algorithm individually.

### Overview

The graph generation process is divided into 6 steps:

1. **Preprocessing** (`step1_preprocess.py`) - Distance transform and obstacle inflation
2. **Skeleton Graph** (`step2_skeleton_graph.py`) - Graph generation from medial axis
3. **Boundary Sampling** (`step3_boundary_sampling.py`) - Add nodes along obstacle boundaries
4. **Free Space Sampling** (`step4_free_space_sampling.py`) - Add nodes in open areas
5. **Delaunay Shortcuts** (`step5_delaunay_shortcuts.py`) - Add shortcuts via triangulation
6. **Graph Pruning** (`step6_prune_graph.py`) - Remove unnecessary nodes/edges and optimize

### Directory Structure

```
scripts/
├── steps/                          # Individual step scripts
│   ├── __init__.py
│   ├── common.py                   # Common utilities
│   ├── step1_preprocess.py         # Step 1: Preprocessing
│   ├── step2_skeleton_graph.py     # Step 2: Skeleton
│   ├── step3_boundary_sampling.py  # Step 3: Boundaries
│   ├── step4_free_space_sampling.py # Step 4: Free space
│   ├── step5_delaunay_shortcuts.py # Step 5: Shortcuts
│   └── step6_prune_graph.py        # Step 6: Pruning
└── run_pipeline.py                 # Pipeline execution script
```

## Usage

### Method 1: Run Complete Pipeline

Run all steps at once:

```bash
python scripts/run_pipeline.py \
  --map data/map.png \
  --output output/ \
  --resolution 0.05 \
  --safety-distance 0.5
```

### Method 2: Run Specific Steps Only

```bash
# Run only steps 1, 2, and 5
python scripts/run_pipeline.py \
  --map data/map.png \
  --output output/ \
  --steps 1,2,5
```

### Method 3: Skip Certain Steps

```bash
# Skip steps 3 and 4
python scripts/run_pipeline.py \
  --map data/map.png \
  --output output/ \
  --skip-steps 3,4
```

### Method 4: Run Each Step Manually

For complete control:

```bash
# Step 1: Preprocessing
python scripts/steps/step1_preprocess.py \
  --map data/map.png \
  --output output/ \
  --resolution 0.05 \
  --safety-distance 0.5

# Step 2: Skeleton Graph
python scripts/steps/step2_skeleton_graph.py \
  --input output/ \
  --output output/ \
  --skeleton-sample-distance 1.5 \
  --visualize

# Step 3: Boundary Sampling
python scripts/steps/step3_boundary_sampling.py \
  --input output/ \
  --output output/ \
  --boundary-inflation-factor 1.5 \
  --boundary-sample-distance 2.5 \
  --visualize

# Step 4: Free Space Sampling
python scripts/steps/step4_free_space_sampling.py \
  --input output/ \
  --output output/ \
  --free-space-sampling-threshold 1.5 \
  --visualize

# Step 5: Delaunay Shortcuts
python scripts/steps/step5_delaunay_shortcuts.py \
  --input output/ \
  --output output/ \
  --visualize

# Step 6: Graph Pruning
python scripts/steps/step6_prune_graph.py \
  --input output/ \
  --output output/ \
  --merge-node-distance 0.25 \
  --min-subgraph-length 0.25 \
  --visualize \
  --output-graph final_graph.pkl
```

## Parameter Details

### Step 1: Preprocessing
- `--map`: Path to occupancy grid map (required)
- `--resolution`: Map resolution (meters/pixel), default: 0.05
- `--safety-distance`: Robot radius (meters), default: 0.5
- `--occupancy-threshold`: Occupancy threshold (0-255), default: 127

### Step 2: Skeleton Graph
- `--skeleton-sample-distance`: Sampling interval along skeleton (meters), default: 1.5
- `--visualize`: Save graph visualization

### Step 3: Boundary Sampling
- `--boundary-inflation-factor`: Boundary inflation factor, default: 1.5
- `--boundary-sample-distance`: Sampling interval along boundaries (meters), default: 2.5
- `--visualize`: Save graph visualization

### Step 4: Free Space Sampling
- `--free-space-sampling-threshold`: Free space detection threshold (meters), default: 1.5
- `--visualize`: Save graph visualization

### Step 5: Delaunay Shortcuts
- `--visualize`: Save graph visualization

### Step 6: Graph Pruning
- `--merge-node-distance`: Maximum distance to merge nodes (meters), default: 0.25
- `--min-subgraph-length`: Minimum subgraph length to keep (meters), default: 0.25
- `--output-graph`: Final graph filename, default: final_graph.pkl
- `--visualize`: Save graph visualization

## Practical Examples

### Example 1: Visualize Each Step for Debugging

```bash
python scripts/run_pipeline.py \
  --map data/map.png \
  --output debug_output/ \
  --visualize-all \
  --log-level DEBUG
```

This saves output images for each step in `debug_output/`:
- `step2_skeleton_graph.png` - Skeleton graph
- `step3_boundary_sampling.png` - After adding boundary nodes
- `step4_free_space_sampling.png` - After adding free space nodes
- `step5_delaunay_shortcuts.png` - After adding shortcuts
- `step6_final_graph.png` - Final graph

### Example 2: Use Only Skeleton and Boundaries

```bash
python scripts/run_pipeline.py \
  --map data/map.png \
  --output output/ \
  --steps 1,2,3,6
```

### Example 3: Experiment with Custom Parameters

```bash
# Generate dense graph
python scripts/run_pipeline.py \
  --map data/map.png \
  --output dense_graph/ \
  --skeleton-sample-distance 0.5 \
  --boundary-sample-distance 1.0 \
  --free-space-sampling-threshold 1.0

# Generate sparse graph
python scripts/run_pipeline.py \
  --map data/map.png \
  --output sparse_graph/ \
  --skeleton-sample-distance 3.0 \
  --boundary-sample-distance 5.0 \
  --free-space-sampling-threshold 3.0
```

### Example 4: Review Step 2 Results Before Continuing

```bash
# First run steps 1-2 and review results
python scripts/run_pipeline.py \
  --map data/map.png \
  --output output/ \
  --steps 1,2 \
  --visualize-all

# After reviewing, run remaining steps
python scripts/run_pipeline.py \
  --map data/map.png \
  --output output/ \
  --steps 3,4,5,6
```

## Intermediate Data

Each step saves intermediate data as `<output_dir>/stepN_data.pkl`:
- `step1_data.pkl` - Preprocessed map and distance transform
- `step2_data.pkl` - Skeleton graph
- `step3_data.pkl` - Graph after adding boundary nodes
- `step4_data.pkl` - Graph after adding free space nodes
- `step5_data.pkl` - Graph after adding shortcuts

The final graph is saved as `final_graph.pkl` and can be loaded as a NetworkX graph object.

## Troubleshooting

### If a Step Fails

```bash
# Run step individually with more detailed logging
python scripts/steps/step2_skeleton_graph.py \
  --input output/ \
  --output output/ \
  --log-level DEBUG
```

### Inspect Intermediate Data

```python
import pickle
import networkx as nx

# Load step 2 data
with open('output/step2_data.pkl', 'rb') as f:
    data = pickle.load(f)

print(f"Nodes: {len(data.graph.nodes)}")
print(f"Edges: {len(data.graph.edges)}")
```
