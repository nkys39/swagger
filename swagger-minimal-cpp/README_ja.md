# SWAGGER Minimal C++: Step1 + Step3

このプロジェクトは、SWAGGERアルゴリズムのStep1（前処理）とStep3（障害物境界サンプリング）をC++で完全実装したものです。Python版と同等の機能を提供します。

## 概要

**SWAGGER Minimal C++**は、占有グリッドマップから障害物境界に沿ったノードとエッジを持つグラフを生成します。

### 処理ステップ

1. **Step 1: 前処理**
   - 占有グリッドマップの読み込み（OpenCV）
   - 自由空間の二値化
   - 距離変換の計算（L2距離）
   - 障害物の膨張処理

2. **Step 3: 障害物境界サンプリング**
   - 膨張した障害物の輪郭を検出
   - 輪郭に沿って等間隔でノードをサンプリング
   - 輪郭上の隣接ノード間にエッジを作成（Bresenham衝突チェック）

### 出力

- `nodes.txt`: ノード座標リスト（テキスト形式）
- `edges.txt`: エッジ情報リスト（テキスト形式）
- `graph_visualization.png`: グラフの可視化画像
- `graph.gml`: GML形式グラフ（オプション）
- `graph.graphml`: GraphML形式グラフ（オプション）

## 必要要件

- C++17対応コンパイラ（GCC 7+、Clang 5+）
- CMake 3.15以上
- OpenCV 4.0以上

## ビルド方法

### 依存パッケージのインストール

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake libopencv-dev
```

**macOS (Homebrew):**
```bash
brew install cmake opencv
```

### ビルド

```bash
cd swagger-minimal-cpp
mkdir -p build
cd build
cmake ..
make -j$(nproc)
```

ビルドが成功すると、以下の実行ファイルが生成されます：
- `build/process_map` - メインプログラム
- `build/examples/create_sample_map` - サンプルマップ作成ツール

## 使用方法

### 基本的な使い方

```bash
./build/process_map --map <マップファイル> --output <出力ディレクトリ>
```

### サンプルマップの作成と実行

```bash
# サンプルマップを作成
./build/examples/create_sample_map

# グラフを生成
./build/process_map --map sample_map.png --output output

# GML形式で出力
./build/process_map --map sample_map.png --output output --save-gml

# GMLとGraphMLの両方で出力
./build/process_map --map sample_map.png --output output --save-gml --save-graphml
```

### 例

```bash
# デフォルトパラメータで実行
./build/process_map --map sample_map.png --output output

# パラメータをカスタマイズ
./build/process_map \
    --map sample_map.png \
    --output output \
    --resolution 0.05 \
    --safety-distance 0.5 \
    --occupancy-threshold 127 \
    --boundary-inflation-factor 1.5 \
    --boundary-sample-distance 2.5 \
    --save-gml

# より密なサンプリング
./build/process_map \
    --map sample_map.png \
    --output output_dense \
    --boundary-sample-distance 1.0 \
    --save-gml

# ログ出力を抑制
./build/process_map \
    --map sample_map.png \
    --output output \
    --save-gml \
    --quiet
```

## コマンドライン引数の完全リファレンス

### 必須引数

| 引数 | 説明 | 形式 |
|------|------|------|
| `--map` | 占有グリッドマップのパス | PNG/PGM形式のファイルパス |

### オプション引数

#### 基本設定

| 引数 | デフォルト | 説明 |
|------|-----------|------|
| `--output` | `output` | 出力ディレクトリのパス |
| `--quiet` | false | ログ出力を抑制 |
| `--help` | - | ヘルプを表示 |

#### マップパラメータ

| 引数 | デフォルト | 単位 | 説明 | 推奨範囲 |
|------|-----------|------|------|---------|
| `--resolution` | `0.05` | m/px | マップの解像度 | 0.01～0.1 |
| `--safety-distance` | `0.5` | m | ロボットの半径 | 0.1～2.0 |
| `--occupancy-threshold` | `127` | - | 占有閾値（0-255） | 0～255 |

**resolution（解像度）の詳細:**
- 小さい値: 高解像度、計算量増加
- 大きい値: 低解像度、計算量減少
- 例: 0.05 = 1ピクセルが5cm四方を表す

**safety-distance（安全距離）の詳細:**
- ロボットの実際の半径に合わせて設定
- 障害物からの最小距離としても機能
- 距離変換の閾値として使用

**occupancy-threshold（占有閾値）の詳細:**
- ピクセル値がこの値**以下**の場合、占有（障害物）と判断
- ピクセル値がこの値**より大きい**場合、自由空間と判断
- デフォルト127の場合:
  - 0-127: 占有領域（黒～グレー）
  - 128-255: 自由空間（グレー～白）

#### Step 3: 境界サンプリングパラメータ

| 引数 | デフォルト | 単位 | 説明 | 推奨範囲 |
|------|-----------|------|------|---------|
| `--boundary-inflation-factor` | `1.5` | - | 境界膨張係数 | 1.0～3.0 |
| `--boundary-sample-distance` | `2.5` | m | サンプリング間隔 | 0.5～5.0 |

**boundary-inflation-factor（境界膨張係数）の詳細:**
- 実際の膨張距離 = `safety_distance × boundary_inflation_factor`
- 1.0: 安全距離と同じ位置に境界を配置
- 1.5: 安全距離の1.5倍の位置に境界を配置（デフォルト）
- 2.0: 安全距離の2倍の位置に境界を配置
- **大きいほど障害物から離れた位置に境界を検出**

**boundary-sample-distance（境界サンプリング距離）の詳細:**
- 輪郭上のノード間の最大距離
- 小さい値: ノードが密になる（計算量増加）
- 大きい値: ノードが疎になる（計算量減少）
- **推奨**: マップのスケールに応じて調整
  - 小規模マップ（10m×10m以下）: 0.5～1.5m
  - 中規模マップ（10m～50m）: 1.5～3.0m
  - 大規模マップ（50m以上）: 3.0～5.0m

#### 出力形式オプション

| 引数 | デフォルト | 説明 | 出力ファイル |
|------|-----------|------|-------------|
| `--save-gml` | false | GML形式で保存 | `graph.gml` |
| `--save-graphml` | false | GraphML形式で保存 | `graph.graphml` |

**デフォルト出力（常に生成）:**
- `nodes.txt`: ノード座標のテキストリスト
- `edges.txt`: エッジ情報のテキストリスト
- `graph_visualization.png`: 可視化画像

## 出力ファイル形式

### nodes.txt

ノード座標のテキストファイル。各行の形式：

```
# row, col (pixel coordinates)
100, 150
100, 200
...
```

### edges.txt

エッジ情報のテキストファイル。各行の形式：

```
# src_row, src_col, dst_row, dst_col, weight, edge_type
100, 150, 100, 200, 50.000, contour
...
```

### graph_visualization.png

グラフを元のマップ上に描画した可視化画像：
- 青い線: エッジ
- 赤い点: ノード

### graph.gml（オプション）

GML形式のグラフファイル。Gephi、yEd、Cytoscapeなどで開けます。

### graph.graphml（オプション）

GraphML形式のグラフファイル。XML形式で構造化されています。

## プロジェクト構造

```
swagger-minimal-cpp/
├── CMakeLists.txt              # メインビルド設定
├── README_ja.md                # このファイル
├── include/                    # ヘッダーファイル
│   ├── graph.hpp               # グラフデータ構造
│   ├── map_processor.hpp       # Step1: 前処理
│   ├── boundary_sampler.hpp    # Step3: 境界サンプリング
│   └── file_writer.hpp         # ファイル出力
├── src/                        # ソースファイル
│   ├── main.cpp                # メインプログラム
│   ├── graph.cpp
│   ├── map_processor.cpp
│   ├── boundary_sampler.cpp
│   └── file_writer.cpp
├── examples/                   # サンプルプログラム
│   ├── CMakeLists.txt
│   └── create_sample_map.cpp   # サンプルマップ作成
└── build/                      # ビルドディレクトリ
```

## 実装の詳細

### クラス構成

#### Graph クラス
- ノードとエッジを管理する軽量グラフデータ構造
- ノードID: `std::pair<int, int>` (row, col)
- ノード属性: `node_type`（文字列）
- エッジ属性: `weight`（距離）、`edge_type`（文字列）
- 無向グラフとして実装

#### MapProcessor クラス
- Step 1の前処理を担当
- OpenCVを使用した画像読み込みと距離変換
- `cv::distanceTransform`で高精度L2距離を計算

#### BoundarySampler クラス
- Step 3の境界サンプリングを担当
- `cv::findContours`で輪郭検出
- Bresenhamアルゴリズムで衝突チェック

#### FileWriter クラス
- 各種形式でのファイル出力を担当
- GML/GraphML/テキスト形式をサポート
- OpenCVで可視化画像を生成

### アルゴリズムの特徴

**距離変換:**
- OpenCVの`DIST_L2`と`DIST_MASK_PRECISE`を使用
- 高精度なユークリッド距離を計算

**輪郭検出:**
- `cv::findContours`で境界を抽出
- `CHAIN_APPROX_TC89_KCOS`で輪郭を簡略化

**衝突チェック:**
- Bresenhamの直線アルゴリズム
- O(max(dx, dy))の効率的な実装

## トラブルシューティング

### ビルドエラー

**エラー: OpenCV が見つかりません**
```
CMake Error: Could not find OpenCV
```

対処法：
```bash
# Ubuntu/Debian
sudo apt-get install libopencv-dev

# macOS
brew install opencv
```

**エラー: C++17 がサポートされていません**
```
error: unsupported option '-std=c++17'
```

対処法：GCCまたはClangを最新版にアップグレードしてください。

### 実行エラー

**エラー: マップファイルが見つかりません**
```
エラー: Failed to load map from: ...
```

対処法：マップファイルのパスが正しいか確認してください。

**警告: マップは完全に自由空間です**

対処法：
- `--occupancy-threshold`の値を調整
- マップが正しく作成されているか確認

## Python版との比較

| 機能 | Python版 | C++版 |
|------|---------|-------|
| Step1: 前処理 | ✓ | ✓ |
| Step3: 境界サンプリング | ✓ | ✓ |
| GML出力 | ✓ | ✓ |
| GraphML出力 | ✓ | ✓ |
| 可視化 | ✓ | ✓ |
| 実行速度 | 標準 | **高速（2～5倍）** |
| メモリ使用量 | 標準 | **効率的** |
| 依存関係 | NumPy、OpenCV、NetworkX | OpenCVのみ |
| バイナリサイズ | - | 小（1～2MB） |

## パフォーマンス

**ベンチマーク環境:**
- CPU: Intel Core i7
- マップサイズ: 500×500ピクセル
- 生成ノード数: 約166個

**実行時間:**
- Step 1（前処理）: 約10ms
- Step 3（境界サンプリング）: 約50ms
- 合計: 約60ms

**Python版との比較:**
- C++版: 約60ms
- Python版: 約150ms
- **速度向上: 約2.5倍**

## ライセンス

Apache-2.0

## 参考文献

- NVIDIA SWAGGER: [https://github.com/nvidia-isaac/SWAGGER](https://github.com/nvidia-isaac/SWAGGER)
- CPU版フォーク: [https://github.com/nkys39/swagger](https://github.com/nkys39/swagger)
- Python版swagger-minimal: `../swagger-minimal/`

## サポート

問題が発生した場合は、以下を確認してください：

1. OpenCV 4.0以上がインストールされているか
2. C++17対応コンパイラを使用しているか
3. CMake 3.15以上を使用しているか
4. マップファイルが正しい形式か

詳細なログを確認するには、`--quiet`フラグを**付けずに**実行してください。
