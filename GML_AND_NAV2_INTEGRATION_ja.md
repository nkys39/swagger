# GML形式とNav2統合ガイド

## GML (Graph Modeling Language) 形式とは

**GML**は、グラフ構造（ノードとエッジ）を表現するための標準的なテキストベースのファイル形式です。

### GML形式の特徴

1. **人間が読みやすい**: テキストベースで構造が明確
2. **標準的**: NetworkXなどの主要なグラフライブラリが対応
3. **拡張可能**: カスタム属性を追加可能
4. **ツールサポート**: 様々なグラフ可視化ツールで読み込み可能

### SWAGGERで生成されるGML形式の構造

```gml
graph [
  directed 0

  node [
    id 0
    label "0"
    world 12.34 56.78 0.0    # ワールド座標 (x, y, z) メートル単位
    pixel 247 1135            # ピクセル座標 (row, col)
  ]

  node [
    id 1
    label "1"
    world 12.45 56.89 0.0
    pixel 249 1137
  ]

  edge [
    source 0
    target 1
    weight 1.52              # エッジの長さ（メートル）
    edge_type "skeleton"     # エッジのタイプ（skeleton/boundary/delaunay/merge）
  ]
]
```

### ノード属性

- **id**: ノードの一意識別子（整数）
- **label**: ノードのラベル（文字列、通常はIDと同じ）
- **world**: ワールド座標 `(x, y, z)` - ロボットが使用する実座標（メートル）
- **pixel**: ピクセル座標 `(row, col)` - 元の地図画像上の位置

### エッジ属性

- **source**: 始点ノードのID
- **target**: 終点ノードのID
- **weight**: エッジの重み（通常は距離、メートル単位）
- **edge_type**: エッジの種類
  - `skeleton`: スケルトングラフから生成
  - `boundary`: 境界サンプリングから生成
  - `delaunay`: Delaunay三角分割によるショートカット
  - `merge`: ノードマージ時に生成
  - `contour`: 輪郭に沿ったエッジ
  - `grid`: グリッドグラフのエッジ（完全自由空間の場合）

## GMLファイルの生成

### 統合スクリプトを使用

```bash
python scripts/generate_graph.py \
    --map-path maps/carter_warehouse_navigation.png \
    --resolution 0.05 \
    --safety-distance 0.3 \
    --output-dir output
```

出力: `output/graph.gml`

### モジュラースクリプトを使用

```bash
# パイプライン全体を実行
python scripts/run_pipeline.py \
    --map maps/carter_warehouse_navigation.png \
    --output output/ \
    --resolution 0.05 \
    --safety-distance 0.3

# 最終ステップでGMLファイルを手動保存
python -c "
import pickle
import networkx as nx
with open('output/final_graph.pkl', 'rb') as f:
    graph = pickle.load(f)
nx.write_gml(graph, 'output/graph.gml')
"
```

## Nav2との統合

Nav2 (Navigation2) は ROS 2 の標準ナビゲーションスタックです。SWAGGERグラフをNav2のグローバルプランナーとして使用できます。

### 統合アーキテクチャ

```
┌─────────────────────┐
│  SWAGGER Library    │
│  (グラフ生成)       │
└──────────┬──────────┘
           │ GMLファイル
           ↓
┌─────────────────────┐
│  GML → GeoJSON      │
│  変換ツール         │
└──────────┬──────────┘
           │ GeoJSON
           ↓
┌─────────────────────┐
│  SWAGGER Planner    │
│  (ROS2 ノード)      │
└──────────┬──────────┘
           │ サービスAPI
           ↓
┌─────────────────────┐
│  Nav2 Global        │
│  Planner Plugin     │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Nav2 Stack         │
│  (ナビゲーション)   │
└─────────────────────┘
```

### ステップ1: GMLからGeoJSONへ変換

Nav2 Route Serverは GeoJSON 形式を使用します。

```bash
python3 integration/nav2/tools/gml_to_geojson.py \
    output/graph.gml \
    -o output/graph.geojson
```

**GeoJSON形式の特徴:**
- EPSG:3857 座標系（Web Mercator）
- ノードは Point フィーチャー
- エッジは LineString フィーチャー（双方向）
- Nav2 Route Serverと互換性あり

### ステップ2: SWAGGERライブラリのインストール

```bash
# 仮想環境を無効化（ROS2はシステムPythonを使用）
deactivate

# SWAGGERをシステムPythonにインストール
pip install -e /path/to/SWAGGER
```

### ステップ3: Nav2パッケージのビルド

```bash
# ROS2ワークスペースで
cd ~/ros2_ws
source /opt/ros/humble/setup.bash

# SWAGGERパッケージをビルド
colcon build --symlink-install --packages-up-to swagger_nav2_bringup

# 環境をソース
source install/setup.bash
```

### ステップ4: Nav2で実行

```bash
ros2 launch swagger_nav2_bringup swagger_with_nav2.launch.py \
    map_yaml:=path/to/map.yaml \
    swagger_planner_config:=path/to/config.yaml
```

## 統合のコンポーネント

### 1. SWAGGER Planner (ROS2 ノード)

`integration/nav2/swagger_planner/`

- SWAGGERライブラリをラップ
- 経路探索APIを提供
- ROS2 サービスインターフェース

### 2. Nav2 Planner Plugin

グローバルプランナープラグインとしてNav2に統合

- SwaggerRoutePlanner クラス
- Nav2の `nav2_core::GlobalPlanner` インターフェースを実装
- SWAGGER Plannerサービスを呼び出し

### 3. 変換ツール

`integration/nav2/tools/gml_to_geojson.py`

- GML → GeoJSON 変換
- EPSG:3857 座標系に対応
- 双方向エッジを生成

## 使用例

### 基本的なワークフロー

```bash
# 1. グラフ生成
python scripts/generate_graph.py \
    --map-path maps/warehouse.png \
    --resolution 0.05 \
    --safety-distance 0.5 \
    --output-dir nav2_graphs

# 2. GeoJSONに変換
python3 integration/nav2/tools/gml_to_geojson.py \
    nav2_graphs/graph.gml \
    -o nav2_graphs/graph.geojson

# 3. Nav2で使用
ros2 launch swagger_nav2_bringup swagger_with_nav2.launch.py \
    map_yaml:=maps/warehouse.yaml \
    swagger_graph:=nav2_graphs/graph.geojson
```

### パラメータのカスタマイズ

**グラフ生成時:**
```bash
python scripts/generate_graph.py \
    --map-path maps/warehouse.png \
    --resolution 0.05 \
    --safety-distance 0.5 \
    --skeleton-sample-distance 1.0 \      # 密なグラフ
    --boundary-sample-distance 1.5 \
    --output-dir dense_graph
```

**Nav2設定ファイル** (`swagger_nav2_config.yaml`):
```yaml
planner_server:
  ros__parameters:
    expected_planner_frequency: 20.0
    planner_plugins: ["GridBased"]
    GridBased:
      plugin: "swagger_nav2_planner_plugin::SwaggerRoutePlanner"
      swagger_service_name: "/generate_route"
      path_simplification: true
```

## トラブルシューティング

### GMLファイルが読み込めない

**症状**: Nav2が起動時にエラー

**解決策**:
1. GMLファイルの構造を確認
```python
import networkx as nx
graph = nx.read_gml('output/graph.gml')
print(f"Nodes: {len(graph.nodes())}")
print(f"Edges: {len(graph.edges())}")
print(graph.nodes(data=True)[0])  # 最初のノードを確認
```

2. 座標が正しいか確認
```python
for node, data in list(graph.nodes(data=True))[:5]:
    print(f"Node {node}: world={data['world']}, pixel={data['pixel']}")
```

### 経路が見つからない

**症状**: Nav2がゴールへの経路を計画できない

**原因**:
- グラフが連結されていない
- ノード密度が低すぎる
- スタート/ゴール位置が障害物に近すぎる

**解決策**:
```bash
# より密なグラフを生成
python scripts/generate_graph.py \
    --map-path maps/warehouse.png \
    --skeleton-sample-distance 0.5 \    # 密に
    --boundary-sample-distance 1.0 \    # 密に
    --free-space-sampling-threshold 1.0 \  # 密に
    --output-dir dense_graph
```

### 座標系の不一致

**症状**: ロボットが正しい位置に移動しない

**解決策**:
- `x_offset`, `y_offset`, `rotation` パラメータを確認
- 地図のoriginとSWAGGERの座標系が一致しているか確認

```bash
python scripts/generate_graph.py \
    --map-path maps/warehouse.png \
    --x-offset 10.0 \      # マップのoriginに合わせる
    --y-offset -5.0 \      # マップのoriginに合わせる
    --rotation 0.0 \       # 必要に応じて回転
    --output-dir output
```

## 他のロボットフレームワークとの統合

### GMLファイルの利用

GMLは標準形式なので、他のフレームワークでも使用可能：

**Python (NetworkX)**:
```python
import networkx as nx

# グラフ読み込み
graph = nx.read_gml('output/graph.gml')

# 経路探索
import nx
path = nx.shortest_path(graph, source=0, target=10, weight='weight')

# ワールド座標を取得
world_coords = [graph.nodes[node]['world'] for node in path]
```

**C++ (Boost Graph Library)**:
```cpp
#include <boost/graph/adjacency_list.hpp>
// GMLパーサーを実装して読み込み
```

**JavaScript (Cytoscape.js)**:
```javascript
// GMLをJSONに変換して可視化
// または cytoscape-gml 拡張を使用
```

## まとめ

**GML形式の利点:**
- ✅ 標準的で互換性が高い
- ✅ 人間が読み書き可能
- ✅ 多くのツールでサポート
- ✅ カスタム属性を追加可能

**Nav2統合の利点:**
- ✅ SWAGGERの高品質グラフをROS2で使用
- ✅ 効率的な経路計画
- ✅ 標準的なNav2インターフェース
- ✅ Isaac SimやGazeboと統合可能

**推奨ワークフロー:**
1. SWAGGERでグラフ生成 → GMLファイル
2. GeoJSONに変換（Nav2の場合）
3. ROS2/Nav2で経路計画に使用
4. 必要に応じてパラメータ調整

## 参考リンク

- [GML形式仕様](http://www.infosun.fim.uni-passau.de/Graphlet/GML/)
- [NetworkX GMLドキュメント](https://networkx.org/documentation/stable/reference/readwrite/gml.html)
- [Nav2ドキュメント](https://docs.nav2.org/)
- [GeoJSON仕様](https://geojson.org/)
