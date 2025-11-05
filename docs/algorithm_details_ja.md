# SWAGGERアルゴリズム詳細解説

このドキュメントでは、SWAGGERアルゴリズムの各ステップの詳細な実装を解説します。

> **親ドキュメント**: [README_ja.md](../README_ja.md)

## 目次

- [ステップ1: 安全バッファの追加](#ステップ1-安全バッファの追加)
- [ステップ2: スケルトングラフの構築](#ステップ2-スケルトングラフの構築)
- [ステップ3: 境界ノードの追加](#ステップ3-境界ノードの追加)
- [ステップ4: 自由空間ノードの追加](#ステップ4-自由空間ノードの追加)
- [ステップ5: Delaunayショートカットの追加](#ステップ5-delaunayショートカットの追加)
- [ステップ6: グラフのプルーニング](#ステップ6-グラフのプルーニング)

---

詳細な実装については、既存の[algorithm.md](algorithm.md)と[tutorial.md](tutorial.md)を参照してください。

このドキュメントは、より技術的な詳細を含む完全版です。

## ステップ1: 安全バッファの追加

**実装**: `scripts/steps/step1_preprocess.py`

### 概要

占有グリッドマップから自由空間を抽出し、ロボットの安全距離に基づいて障害物を膨張させます。

### 主な処理

1. **マップの読み込み**: PGM/PNG形式の占有グリッドマップを読み込み
2. **二値化**: 占有閾値に基づいて自由空間と障害物を分離
3. **距離変換**: OpenCVの`distanceTransform`で各自由空間ピクセルから最寄り障害物までの距離を計算
4. **膨張**: ロボットの半径（safety_distance）内のピクセルを障害物としてマーク

### パラメータ

- `resolution`: マップの解像度（m/px）
- `safety_distance`: ロボットの半径（m）
- `occupancy_threshold`: 占有閾値（0-255、デフォルト:127）

### 出力

- `original_map`: 元の占有グリッドマップ
- `free_map`: 二値化された自由空間マップ
- `dist_transform`: 距離変換マップ
- `inflated_map`: 膨張障害物マップ

詳細は`docs/ALGORITHM_STEPS_USAGE.md`を参照してください。

---

## ステップ2: スケルトングラフの構築

**実装**: `scripts/steps/step2_skeleton_graph.py`

### 概要

medial axis（中心線）に沿ってノードとエッジを配置します。

### アルゴリズム

1. **スケルトン化**: scikit-imageの`skeletonize`でmedial axisを抽出
2. **分岐解析**: skanライブラリでスケルトンの分岐（パス）を検出
3. **ノード配置**: 各パスに沿って等間隔でノードを配置
4. **エッジ生成**: 隣接ノード間をエッジで接続（衝突チェック付き）

### パラメータ

- `skeleton_sample_distance`: ノード間のサンプリング距離（m、デフォルト:1.5）

### C++実装の特徴

C++版（`swagger-cpp`）では、scikit-imageと**完全一致する**カスタムZhang-Suenスケルトン化を実装：
- 256要素のルックアップテーブル（LUT）
- 2段階の反復的細線化
- ビット単位でPython実装と一致

詳細は`swagger-cpp/README_ja.md`を参照してください。

---

## ステップ3: 境界ノードの追加

**実装**: `scripts/steps/step3_boundary_sampling.py`

### 概要

障害物の境界に沿ってノードを配置し、カバレッジを改善します。

### 処理フロー

1. **輪郭検出**: OpenCVの`findContours`で膨張障害物の輪郭を検出
2. **サンプリング**: 輪郭に沿って等間隔でノードを配置
3. **エッジ生成**: 輪郭上の隣接ノード間をエッジで接続

### パラメータ

- `boundary_inflation_factor`: 境界膨張係数（デフォルト:1.5）
- `boundary_sample_distance`: サンプリング距離（m、デフォルト:2.5）

---

## ステップ4: 自由空間ノードの追加

**実装**: `scripts/steps/step4_free_space_sampling.py`

### 概要

大きな自由空間領域にノードを追加し、グラフの密度を向上させます。

### アルゴリズム

反復的なlocal maximaサンプリング：

```python
while True:
    # 既存ノードからの距離マップを計算
    distance_map = cv2.distanceTransform(...)

    # 大きな距離領域を検出
    large_distance_areas = (distance_map > threshold)

    # Local maximaを検出
    local_maxima = find_local_maxima(large_distance_areas)

    # ノードを追加
    for coord in local_maxima:
        if no_nearby_nodes(coord):
            graph.add_node(coord)

    # 収束判定
    if no_nodes_added:
        break
```

### パラメータ

- `free_space_sampling_threshold`: 距離閾値（m、デフォルト:1.5）

### C++実装との一致

- Python: `while True`で収束まで無限ループ
- C++: `max_iterations = 10000`で実質的に同じ動作
- **エッジは追加しない**（Step5で追加）

---

## ステップ5: Delaunayショートカットの追加

**実装**: `scripts/steps/step5_delaunay_shortcuts.py`

### 概要

Delaunay三角分割を使用してショートカットエッジを追加し、経路の効率を向上させます。

### 処理

1. **三角分割**: 全ノードに対してDelaunay三角分割を実行
2. **エッジ抽出**: 三角形のエッジを候補として抽出
3. **衝突チェック**: 各エッジが障害物と衝突しないか確認
4. **エッジ追加**: 有効なエッジのみをグラフに追加

### 実装

- Python: `scipy.spatial.Delaunay`
- C++: `cv::Subdiv2D`

---

## ステップ6: グラフのプルーニング

**実装**: `scripts/steps/step6_prune_graph.py`

### 概要

近接ノードを統合し、小さなサブグラフを削除してグラフを最適化します。

### 処理

1. **ノードマージ**: 近接ノード（merge_distance未満）を統合
2. **サブグラフ削除**: 小さなサブグラフ（min_subgraph_length未満）を削除
3. **座標変換**: ピクセル座標をワールド座標に変換

### パラメータ

- `merge_distance`: ノードマージ距離（m、デフォルト:0.25）
- `min_subgraph_length`: 最小サブグラフ長（m、デフォルト:0.25）
- `x_offset`, `y_offset`, `rotation`: ワールド座標変換パラメータ

---

## 処理負荷ランキング

各ステップの計算コストと最適化の詳細については、[performance_ja.md](performance_ja.md)を参照してください。

## 関連ドキュメント

- [algorithm.md](algorithm.md) - アルゴリズム概要（英語）
- [tutorial.md](tutorial.md) - チュートリアル（英語）
- [MODULAR_USAGE.md](MODULAR_USAGE.md) - モジュラー実行ガイド
- [ALGORITHM_STEPS_USAGE.md](ALGORITHM_STEPS_USAGE.md) - 各ステップの詳細な使い方
