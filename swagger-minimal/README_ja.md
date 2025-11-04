# SWAGGER Minimal: Step1 + Step3

このプロジェクトは、SWAGGERアルゴリズムのStep1（前処理）とStep3（障害物境界サンプリング）を統合した、軽量で簡単に使えるグラフ生成ツールです。

## 概要

**SWAGGER Minimal**は、占有グリッドマップから障害物境界に沿ったノードとエッジを持つグラフを生成します。

### 処理ステップ

1. **Step 1: 前処理**
   - 占有グリッドマップの読み込み
   - 自由空間の二値化
   - 距離変換の計算
   - 障害物の膨張処理

2. **Step 3: 障害物境界サンプリング**
   - 膨張した障害物の輪郭を検出
   - 輪郭に沿って等間隔でノードをサンプリング
   - 輪郭上の隣接ノード間にエッジを作成

### 出力

- `graph.pkl`: NetworkXグラフ（Pickle形式）
- `nodes.txt`: ノード座標リスト（テキスト形式）
- `edges.txt`: エッジ情報リスト（テキスト形式）
- `graph_visualization.png`: グラフの可視化画像

## クイックスタート

```bash
# 1. uvのインストール（まだの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. プロジェクトディレクトリに移動
cd swagger-minimal

# 3. 依存パッケージをインストール
uv sync

# 4. 仮想環境を有効化
source .venv/bin/activate

# 5. サンプルマップを作成
python create_sample_map.py

# 6. グラフを生成（GML形式でも出力）
python process_map.py --map maps/sample_map.png --output output --save-gml

# 7. 結果を確認
python example_usage.py

# 8. 生成されたファイルを確認
ls -lh output/
```

## 必要要件

- Python 3.10以上
- uv (推奨) またはpip

## セットアップ

### uvを使用する場合（推奨）

```bash
# uvのインストール（まだの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# プロジェクトディレクトリに移動
cd swagger-minimal

# 依存パッケージのインストール
uv sync

# 仮想環境を有効化
source .venv/bin/activate
```

### pipを使用する場合

```bash
# プロジェクトディレクトリに移動
cd swagger-minimal

# 仮想環境の作成
python3 -m venv .venv

# 仮想環境を有効化
source .venv/bin/activate

# 依存パッケージのインストール
pip install -e .
```

## 使用方法

### 基本的な使い方

```bash
python process_map.py --map <マップファイル> --output <出力ディレクトリ>
```

### 例

```bash
# デフォルトパラメータで実行
python process_map.py --map maps/sample_map.png --output output

# GML形式で出力
python process_map.py --map maps/sample_map.png --output output --save-gml

# GMLとGraphMLの両方で出力
python process_map.py --map maps/sample_map.png --output output --save-gml --save-graphml

# パラメータをカスタマイズして実行
python process_map.py \
    --map maps/sample_map.png \
    --output output \
    --resolution 0.05 \
    --safety-distance 0.5 \
    --occupancy-threshold 127 \
    --boundary-inflation-factor 1.5 \
    --boundary-sample-distance 2.5 \
    --save-gml

# より密なサンプリングでGML出力
python process_map.py \
    --map maps/sample_map.png \
    --output output_dense \
    --boundary-sample-distance 1.0 \
    --save-gml

# より粗いサンプリング
python process_map.py \
    --map maps/sample_map.png \
    --output output_sparse \
    --boundary-sample-distance 5.0

# 境界を障害物に近づける
python process_map.py \
    --map maps/sample_map.png \
    --output output_close \
    --boundary-inflation-factor 1.0 \
    --save-gml

# デバッグモードで詳細ログを出力
python process_map.py \
    --map maps/sample_map.png \
    --output output \
    --log-level DEBUG
```

## コマンドライン引数の完全リファレンス

### 必須引数

| 引数 | 説明 | 形式 |
|------|------|------|
| `--map` | 占有グリッドマップのパス | PNG/PGM形式のファイルパス |

### オプション引数

#### 基本設定

| 引数 | デフォルト | 説明 | 備考 |
|------|-----------|------|------|
| `--output` | `output` | 出力ディレクトリのパス | 相対パスまたは絶対パス |
| `--log-level` | `INFO` | ログレベル | `DEBUG`, `INFO`, `WARNING`, `ERROR` から選択 |

#### マップパラメータ

| 引数 | デフォルト | 単位 | 説明 | 推奨範囲 |
|------|-----------|------|------|---------|
| `--resolution` | `0.05` | m/px | マップの解像度（メートル/ピクセル） | 0.01～0.1 |
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
| `--boundary-inflation-factor` | `1.5` | - | 境界膨張係数（無次元） | 1.0～3.0 |
| `--boundary-sample-distance` | `2.5` | m | 輪郭に沿ったサンプリング間隔 | 0.5～5.0 |

**boundary-inflation-factor（境界膨張係数）の詳細:**
- 実際の膨張距離 = `safety_distance × boundary_inflation_factor`
- 1.0: 安全距離と同じ位置に境界を配置
- 1.5: 安全距離の1.5倍の位置に境界を配置（デフォルト）
- 2.0: 安全距離の2倍の位置に境界を配置
- **大きいほど障害物から離れた位置に境界を検出**
- 小さすぎると障害物に近すぎて危険
- 大きすぎると有効な領域が減少

**boundary-sample-distance（境界サンプリング距離）の詳細:**
- 輪郭上のノード間の最大距離
- 小さい値: ノードが密になり、詳細な境界を表現（計算量増加）
- 大きい値: ノードが疎になり、簡略化された境界（計算量減少）
- **推奨**: マップのスケールに応じて調整
  - 小規模マップ（10m×10m以下）: 0.5～1.5m
  - 中規模マップ（10m～50m）: 1.5～3.0m
  - 大規模マップ（50m以上）: 3.0～5.0m

#### 出力形式オプション

| 引数 | デフォルト | 説明 | 出力ファイル |
|------|-----------|------|-------------|
| `--save-gml` | False | GML形式でグラフを保存 | `graph.gml` |
| `--save-graphml` | False | GraphML形式でグラフを保存 | `graph.graphml` |

**GML（Graph Modeling Language）形式:**
- 標準的なグラフ記述言語
- テキストベースで人間が読める
- Gephi、yEd、Cytoscapeなどで使用可能
- ノード・エッジ属性を保持

**GraphML形式:**
- XML形式のグラフ記述言語
- より構造化されたフォーマット
- 多くのグラフ可視化ツールでサポート
- 複雑な属性やメタデータに対応

**デフォルト出力（常に生成）:**
- `graph.pkl`: NetworkX Pickle形式（Python専用）
- `nodes.txt`: ノード座標のテキストリスト
- `edges.txt`: エッジ情報のテキストリスト
- `graph_visualization.png`: 可視化画像

## 出力ファイル形式

### graph.pkl

NetworkXグラフのPickle形式。Pythonで読み込んで使用できます：

```python
import pickle
import networkx as nx

with open('output/graph.pkl', 'rb') as f:
    graph = pickle.load(f)

print(f"ノード数: {len(graph.nodes)}")
print(f"エッジ数: {len(graph.edges)}")
```

### nodes.txt

ノード座標のテキストファイル。各行の形式：

```
# row, col (pixel coordinates)
100, 150
100, 200
...
```

- `row`: 行座標（ピクセル、Y軸）
- `col`: 列座標（ピクセル、X軸）

### edges.txt

エッジ情報のテキストファイル。各行の形式：

```
# src_row, src_col, dst_row, dst_col, weight, edge_type
100, 150, 100, 200, 50.000, contour
...
```

- `src_row, src_col`: 始点ノードの座標
- `dst_row, dst_col`: 終点ノードの座標
- `weight`: エッジの重み（ピクセル単位の距離）
- `edge_type`: エッジの種類（`contour`=輪郭エッジ）

### graph_visualization.png

グラフを元のマップ上に描画した可視化画像：

- 青い線: エッジ
- 赤い点: ノード

### graph.gml（オプション）

`--save-gml`フラグを使用した場合に生成されるGML形式のファイル。

**特徴:**
- テキストベースで人間が読める
- グラフ可視化ツール（Gephi、yEd、Cytoscape）で直接開ける
- ノード・エッジの属性が保持される

**GMLファイルの例:**
```gml
graph [
  node [
    id 0
    label "(235, 295)"
  ]
  node [
    id 1
    label "(235, 350)"
  ]
  edge [
    source 0
    target 1
    weight 55.0
    edge_type "contour"
  ]
]
```

**使用方法:**
```bash
# GML形式で保存
python process_map.py --map maps/sample_map.png --output output --save-gml

# GMLファイルを読み込み
import networkx as nx
graph = nx.read_gml('output/graph.gml')
```

### graph.graphml（オプション）

`--save-graphml`フラグを使用した場合に生成されるGraphML形式のファイル。

**特徴:**
- XML形式で構造化されている
- より多くのメタデータを保存可能
- 国際標準のグラフ交換フォーマット
- Gephi、Cytoscape、igraphなどで使用可能

**GraphMLファイルの例:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>
  <key id="edge_type" for="edge" attr.name="edge_type" attr.type="string"/>
  <graph edgedefault="undirected">
    <node id="0"/>
    <node id="1"/>
    <edge source="0" target="1">
      <data key="weight">55.0</data>
      <data key="edge_type">contour</data>
    </edge>
  </graph>
</graphml>
```

**使用方法:**
```bash
# GraphML形式で保存
python process_map.py --map maps/sample_map.png --output output --save-graphml

# GraphMLファイルを読み込み
import networkx as nx
graph = nx.read_graphml('output/graph.graphml')
```

## マップファイルの準備

### サポートされる形式

- PNG形式（推奨）
- PGM形式

### マップの要件

- グレースケール画像（0-255の値）
- ピクセル値の意味：
  - **0-127**: 占有領域（障害物）
  - **128-255**: 自由空間

### サンプルマップの作成

簡単なテストマップを作成する例：

```python
import cv2
import numpy as np

# 空白マップを作成（500x500、すべて白=自由空間）
map_img = np.ones((500, 500), dtype=np.uint8) * 255

# 矩形の障害物を追加（黒=占有）
cv2.rectangle(map_img, (100, 100), (400, 150), 0, -1)
cv2.rectangle(map_img, (100, 200), (150, 400), 0, -1)
cv2.rectangle(map_img, (300, 250), (400, 400), 0, -1)

# 円形の障害物を追加
cv2.circle(map_img, (250, 350), 50, 0, -1)

# 保存
cv2.imwrite('sample_map.png', map_img)
```

## トラブルシューティング

### エラー: "マップファイルが見つかりません"

- マップファイルのパスが正しいか確認してください
- 相対パスまたは絶対パスを使用できます

### エラー: "マップの読み込みに失敗しました"

- ファイルが破損していないか確認してください
- サポートされる形式（PNG/PGM）を使用しているか確認してください

### 警告: "マップは完全に自由空間です"

- マップに障害物が検出されませんでした
- `--occupancy-threshold`の値を調整してみてください
- マップが正しく作成されているか確認してください

### ノード数を調整したい

パラメータの調整については、上記の「コマンドライン引数の完全リファレンス」を参照してください。

**ノード数に影響するパラメータ:**
- `--boundary-sample-distance`: 小さいほどノードが増える
- `--boundary-inflation-factor`: 境界の位置を調整（間接的に影響）

### GML/GraphML保存でエラーが出る

**原因:**
- ノード名やエッジ属性に特殊文字が含まれている可能性

**対処法:**
- エラーメッセージを確認してください
- デバッグモード（`--log-level DEBUG`）で詳細を確認
- Pickle形式（`graph.pkl`）は常に動作します

## アルゴリズムの詳細

### Step 1: 前処理

1. **占有グリッドの読み込み**
   - PNG/PGMファイルからグレースケール画像として読み込み

2. **二値化**
   - `occupancy_threshold`を基準に自由空間と占有空間を分離
   - `value > threshold` → 自由空間（1）
   - `value ≤ threshold` → 占有空間（0）

3. **距離変換**
   - OpenCVの`distanceTransform`を使用
   - L2距離（ユークリッド距離）で計算
   - 各自由空間ピクセルから最寄りの障害物までの距離を算出

4. **障害物の膨張**
   - `safety_distance`を閾値として二値化
   - ロボットが安全に移動できる領域を計算

### Step 3: 障害物境界サンプリング

1. **輪郭検出**
   - 距離変換マップから`boundary_inflation_factor × safety_distance`の等高線を検出
   - OpenCVの`findContours`を使用
   - 近似アルゴリズム: `CHAIN_APPROX_TC89_KCOS`（点数を削減）

2. **ノードのサンプリング**
   - 各輪郭の頂点をノードとして追加
   - 頂点間の距離が`boundary_sample_distance`を超える場合、中間点を補間
   - `np.linspace`で等間隔に配置

3. **エッジの作成**
   - 輪郭上の連続するノード間にエッジを作成
   - Bresenhamアルゴリズムで衝突チェック
   - 障害物と交差しないエッジのみを追加
   - エッジの重み = ユークリッド距離（ピクセル単位）

## 応用例

### 生成したグラフの利用

```python
import pickle
import networkx as nx
import matplotlib.pyplot as plt

# グラフを読み込み
with open('output/graph.pkl', 'rb') as f:
    graph = pickle.load(f)

# グラフの統計情報を表示
print(f"ノード数: {len(graph.nodes)}")
print(f"エッジ数: {len(graph.edges)}")
print(f"連結成分数: {nx.number_connected_components(graph)}")

# 次数分布を表示
degrees = [graph.degree(n) for n in graph.nodes()]
plt.hist(degrees, bins=range(0, max(degrees)+2))
plt.xlabel('次数')
plt.ylabel('ノード数')
plt.title('次数分布')
plt.savefig('degree_distribution.png')
```

### GML/GraphML形式の読み込みと活用

```python
import networkx as nx

# GML形式から読み込み
graph_gml = nx.read_gml('output/graph.gml')
print(f"GMLから読み込み: {len(graph_gml.nodes)}ノード, {len(graph_gml.edges)}エッジ")

# GraphML形式から読み込み
graph_graphml = nx.read_graphml('output/graph.graphml')
print(f"GraphMLから読み込み: {len(graph_graphml.nodes)}ノード, {len(graph_graphml.edges)}エッジ")

# エッジ属性を確認
for src, dst, data in list(graph_gml.edges(data=True))[:3]:
    print(f"エッジ: {src} -> {dst}, 重み={data.get('weight', 0):.2f}, タイプ={data.get('edge_type', 'unknown')}")
```

### GML形式への変換（Pickleから）

```python
import pickle
import networkx as nx

# Pickleグラフを読み込み
with open('output/graph.pkl', 'rb') as f:
    graph = pickle.load(f)

# GML形式で保存
nx.write_gml(graph, 'output/graph.gml')
print("GML形式で保存しました: output/graph.gml")

# GraphML形式でも保存
nx.write_graphml(graph, 'output/graph.graphml')
print("GraphML形式で保存しました: output/graph.graphml")
```

### 最短経路の計算

```python
import pickle
import networkx as nx

# グラフを読み込み
with open('output/graph.pkl', 'rb') as f:
    graph = pickle.load(f)

# 任意の2ノード間の最短経路を計算
nodes = list(graph.nodes())
if len(nodes) >= 2:
    start = nodes[0]
    goal = nodes[-1]

    try:
        path = nx.shortest_path(graph, start, goal, weight='weight')
        print(f"最短経路: {len(path)}ノード")
        print(f"経路長: {nx.shortest_path_length(graph, start, goal, weight='weight'):.2f}px")
    except nx.NetworkXNoPath:
        print("経路が見つかりませんでした")
```

## ライセンス

Apache-2.0

## 参考文献

- NVIDIA SWAGGER: [https://github.com/nvidia-isaac/SWAGGER](https://github.com/nvidia-isaac/SWAGGER)
- CPU版フォーク: [https://github.com/nkys39/swagger](https://github.com/nkys39/swagger)

## サポート

問題が発生した場合は、以下を確認してください：

1. Python 3.10以上を使用しているか
2. 必要なパッケージがすべてインストールされているか
3. マップファイルが正しい形式か
4. パラメータが適切な範囲内か

詳細なログを確認するには、`--log-level DEBUG`を使用してください。
