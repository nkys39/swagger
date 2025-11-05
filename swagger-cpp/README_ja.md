#  SWAGGER C++: Python実装との比較・検証用完全実装

このプロジェクトは、SWAGGERアルゴリズムの全6ステップをC++で完全実装したもので、**Python実装との動作比較・検証を目的**としています。

## 概要

**SWAGGER C++**は、占有グリッドマップから疎なウェイポイントグラフを生成する完全なパイプラインです。Python (scikit-image) 実装と**ビット単位で一致する結果**を生成するように設計されています。

### 主な目的

1. **Python実装の検証**: 各ステップの出力をPythonと比較
2. **アルゴリズム理解**: C++実装を通じてアルゴリズムの詳細を理解
3. **性能評価**: Python版とC++版の性能を比較
4. **参照実装**: 他のプラットフォームへの移植の参考

### 重要な特徴

- **完全互換のZhang-Suenスケルトン化**: scikit-imageと同じLUT（ルックアップテーブル）を使用
- **デバッグ出力**: 各ステップで中間結果を`debug_output/`に保存
- **比較ツール対応**: `tools/`のスクリプトでPythonと比較可能

### 処理ステップ

1. **Step 1: 前処理**
   - 占有グリッドマップの読み込み
   - 距離変換の計算（L2距離）
   - 障害物の膨張処理

2. **Step 2: スケルトングラフ生成**
   - **カスタムZhang-Suenスケルトン化**: scikit-imageと完全一致する独自実装
   - 256要素LUTによる高速化
   - スケルトンに沿ったノード配置
   - エッジ接続

3. **Step 3: 境界サンプリング**
   - 障害物輪郭の検出
   - 境界に沿ったノード配置
   - 輪郭エッジの生成

4. **Step 4: 自由空間サンプリング**
   - 大きな自由空間領域の検出
   - 局所最大値にノードを配置
   - 反復的サンプリング

5. **Step 5: Delaunayショートカット**
   - Delaunay三角形分割
   - ショートカットエッジの追加
   - 衝突チェック

6. **Step 6: グラフプルーニング**
   - 近接ノードのマージ
   - 小サブグラフの削除
   - ワールド座標への変換

### 出力

- `nodes.txt`: ノード座標リスト
- `edges.txt`: エッジ情報リスト
- `graph.gml`: GML形式グラフ
- `graph.graphml`: GraphML形式グラフ
- `graph_visualization.png`: 可視化画像

## 必要要件

- C++17対応コンパイラ（GCC 7+、Clang 5+）
- CMake 3.15以上
- OpenCV 4.0以上

## ビルド方法

```bash
# 依存パッケージのインストール
sudo apt-get install -y build-essential cmake libopencv-dev

# ビルド
cd swagger-cpp
mkdir build && cd build
cmake ..
make -j$(nproc)
```

## 使用方法

```bash
# デフォルト設定で実行（全ステップ）
./generate_graph --map <マップファイル> --output <出力ディレクトリ>

# GML/GraphML形式で出力
./generate_graph --map sample_map.png --output output --save-gml --save-graphml

# 特定のステップのみ実行
./generate_graph --map sample_map.png --output output \
    --use-skeleton \
    --use-boundary \
    --use-free-space \
    --use-delaunay \
    --prune-graph
```

## コマンドライン引数

### 必須引数
- `--map <パス>` - 占有グリッドマップのパス

### 基本設定
- `--output <パス>` - 出力ディレクトリ（デフォルト: output）
- `--resolution <値>` - 解像度（m/px、デフォルト: 0.05）
- `--safety-distance <値>` - ロボット半径（m、デフォルト: 0.5）
- `--occupancy-threshold <値>` - 占有閾値（0-255、デフォルト: 127）

### ステップ制御
- `--use-skeleton` - Step2を有効化（デフォルト: true）
- `--use-boundary` - Step3を有効化（デフォルト: true）
- `--use-free-space` - Step4を有効化（デフォルト: true）
- `--use-delaunay` - Step5を有効化（デフォルト: true）
- `--prune-graph` - Step6を有効化（デフォルト: true）

### Step2パラメータ
- `--skeleton-sample-distance <値>` - サンプリング距離（m、デフォルト: 1.5）

### Step3パラメータ
- `--boundary-inflation-factor <値>` - 境界膨張係数（デフォルト: 1.5）
- `--boundary-sample-distance <値>` - サンプリング距離（m、デフォルト: 2.5）

### Step4パラメータ
- `--free-space-threshold <値>` - 距離閾値（m、デフォルト: 1.5）

### Step6パラメータ
- `--merge-distance <値>` - ノードマージ距離（m、デフォルト: 0.25）
- `--min-subgraph-length <値>` - 最小サブグラフ長（m、デフォルト: 0.25）

### 出力形式
- `--save-gml` - GML形式で保存
- `--save-graphml` - GraphML形式で保存
- `--quiet` - ログ出力を抑制

## プロジェクト構造

```
swagger-cpp/
├── CMakeLists.txt              # メインビルド設定
├── README_ja.md                # このファイル
├── include/                    # ヘッダーファイル
│   ├── graph.hpp               # グラフデータ構造
│   ├── utils.hpp               # 共通ユーティリティ
│   ├── step1_preprocess.hpp    # Step1: 前処理
│   ├── step2_skeleton.hpp      # Step2: スケルトン
│   ├── step3_boundary.hpp      # Step3: 境界サンプリング
│   ├── step4_free_space.hpp    # Step4: 自由空間
│   ├── step5_delaunay.hpp      # Step5: Delaunay
│   ├── step6_prune.hpp         # Step6: プルーニング
│   └── file_writer.hpp         # ファイル出力
├── src/                        # ソースファイル
│   ├── main.cpp                # メインプログラム
│   ├── graph.cpp
│   ├── utils.cpp
│   ├── step1_preprocess.cpp
│   ├── step2_skeleton.cpp
│   ├── step3_boundary.cpp
│   ├── step4_free_space.cpp
│   ├── step5_delaunay.cpp
│   ├── step6_prune.cpp
│   └── file_writer.cpp
└── examples/                   # サンプルプログラム
    └── create_sample_map.cpp
```

## 実装状況

| ステップ | 状態 | 説明 |
|---------|------|------|
| Step1 | ✅ 完成 | 前処理・距離変換（OpenCV distanceTransform） |
| Step2 | ✅ 完成 | **カスタムZhang-Suenスケルトン化**（scikit-image互換） |
| Step3 | ✅ 完成 | 境界サンプリング（Bresenham衝突検出） |
| Step4 | ✅ 完成 | 自由空間サンプリング（Python完全一致） |
| Step5 | ✅ 完成 | Delaunayショートカット（cv::Subdiv2D） |
| Step6 | ✅ 完成 | グラフプルーニング（ノード統合・世界座標変換） |
| File I/O | ✅ 完成 | GML/GraphML/テキスト出力 |
| デバッグ出力 | ✅ 完成 | 各ステップの中間結果保存 |

**全ステップ完全実装済み！Python実装との比較検証可能！**

## Python版との比較・検証

### 比較方法

```bash
# 1. Python版を実行
cd /path/to/swagger
python scripts/run_pipeline.py --map data/maps/example.pgm --output output/python

# 2. C++版を実行
cd swagger-cpp/build
./swagger_cpp --map ../../data/maps/example.pgm --output ../../output/cpp

# 3. 比較ツールで検証
cd ../..
python tools/compare_step_by_step.py
python tools/compare_distance_transform.py
```

### 機能比較

| 機能 | Python版 | C++版 |
|------|---------|-------|
| 全ステップ実装 | ✓ | ✓ **完成** |
| Zhang-Suenスケルトン化 | scikit-image | **カスタム実装（互換）** |
| 結果の一致性 | 基準 | **ビット単位で一致** |
| 実行速度 | 標準 | 2～5倍高速（予想） |
| メモリ使用 | 標準 | より効率的 |
| 依存関係 | NumPy、OpenCV、NetworkX、skan | **OpenCVのみ** |
| GML/GraphML出力 | ✓ | ✓ |
| デバッグ出力 | ✓ | ✓ |

### 比較ツール

詳細は `../../tools/README.md` を参照してください：

- `compare_distance_transform.py` - Step1の距離変換を比較
- `compare_step_by_step.py` - 全ステップを段階的に比較
- `visualize_steps.py` - ステップごとの可視化

## 開発ロードマップ

### Phase 1: 基本実装 ✅
- [x] プロジェクト構造
- [x] Graph クラス
- [x] Step1 前処理
- [x] Step3 境界サンプリング
- [x] File I/O (GML/GraphML)

### Phase 2: コア機能 ✅
- [x] Step2 スケルトン生成
- [x] Step4 自由空間サンプリング
- [x] Step5 Delaunay三角形分割
- [x] Step6 グラフプルーニング

### Phase 3: 最適化
- [ ] 性能最適化
- [ ] 並列処理対応
- [ ] メモリ効率化

## ライセンス

Apache-2.0

## 参考文献

- NVIDIA SWAGGER: https://github.com/nvidia-isaac/SWAGGER
- CPU版フォーク: https://github.com/nkys39/swagger
- Python版swagger-minimal: ../swagger-minimal/
- C++版swagger-minimal: ../swagger-minimal-cpp/

## 貢献

コントリビューションを歓迎します：
1. 性能最適化
2. テストケースの追加
3. ドキュメントの改善
4. 追加機能の実装
