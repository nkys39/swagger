# GML可視化ツールガイド

GML (Graph Modeling Language) 形式をサポートする可視化ツールとその使い方を紹介します。

## 目次
- [デスクトップツール](#デスクトップツール)
- [Pythonライブラリ](#pythonライブラリ)
- [Webベースツール](#webベースツール)
- [コマンドラインツール](#コマンドラインツール)
- [推奨ツール比較](#推奨ツール比較)
- [C++での処理](GML_CPP_GUIDE_ja.md) - C++でGMLファイルを読み込み・処理する方法

---

## デスクトップツール

### 1. Gephi（最も人気）⭐

**特徴:**
- ✅ 無料・オープンソース
- ✅ 強力なレイアウトアルゴリズム（Force Atlas 2など）
- ✅ インタラクティブな可視化
- ✅ 大規模グラフに対応（数百万ノード）
- ✅ プラグインエコシステム

**インストール:**
```bash
# Ubuntu
sudo apt install gephi

# または公式サイトからダウンロード
# https://gephi.org/
```

**使い方:**
```
1. Gephiを起動
2. File → Open → graph.gml を選択
3. Layout → Force Atlas 2 を選択して "Run" をクリック
4. ノードサイズ、色などをカスタマイズ
5. File → Export → SVG/PNG で画像出力
```

**SWAGGERグラフの可視化設定:**
```
- Layout: Force Atlas 2 (推奨) または Yifan Hu
- Node size: Degree (次数)に応じて
- Node color: edge_type属性で色分け
- Edge weight: weight属性を使用
```

**出力例:**
- PNG, SVG, PDF形式
- インタラクティブなHTML
- 動画出力も可能

---

### 2. yEd Graph Editor

**特徴:**
- ✅ 無料
- ✅ きれいな自動レイアウト
- ✅ 直感的なUI
- ✅ Windows/Mac/Linux対応

**インストール:**
```bash
# 公式サイトからダウンロード
# https://www.yworks.com/products/yed
```

**使い方:**
```
1. yEdを起動
2. File → Open → graph.gml を選択
3. Layout → Hierarchical/Organic を選択
4. F2キーでレイアウト適用
5. File → Export → PNG/SVG
```

**特徴的なレイアウト:**
- Hierarchical: 階層構造を持つグラフに最適
- Organic: 自然な配置
- Circular: 円形配置
- Orthogonal: 直角エッジ

---

### 3. Cytoscape

**特徴:**
- ✅ 無料・オープンソース
- ✅ バイオインフォマティクス向けだが汎用的
- ✅ 豊富なプラグイン
- ✅ 統計分析機能

**インストール:**
```bash
# 公式サイトからダウンロード
# https://cytoscape.org/
```

**使い方:**
```
1. Cytoscapeを起動
2. File → Import → Network from File → graph.gml
3. Layout → Prefuse Force Directed Layout
4. Style タブでビジュアライズ設定
5. File → Export as Image
```

---

## Pythonライブラリ

### 1. NetworkX + Matplotlib（最も簡単）⭐

**インストール:**
```bash
pip install networkx matplotlib
```

**基本的な可視化:**
```python
import networkx as nx
import matplotlib.pyplot as plt

# GMLファイルを読み込み
graph = nx.read_gml('output/graph.gml')

# 基本的な可視化
plt.figure(figsize=(12, 8))
pos = nx.spring_layout(graph, k=0.5, iterations=50)
nx.draw_networkx_nodes(graph, pos, node_size=50, node_color='lightblue')
nx.draw_networkx_edges(graph, pos, alpha=0.5, width=0.5)
plt.axis('off')
plt.tight_layout()
plt.savefig('graph_visualization.png', dpi=300, bbox_inches='tight')
plt.show()
```

**エッジタイプで色分け:**
```python
import networkx as nx
import matplotlib.pyplot as plt

graph = nx.read_gml('output/graph.gml')

# エッジタイプごとに色を設定
edge_colors = {
    'skeleton': 'red',
    'boundary': 'blue',
    'delaunay': 'green',
    'merge': 'orange',
    'contour': 'purple'
}

plt.figure(figsize=(15, 10))
pos = nx.spring_layout(graph, k=0.5, iterations=50)

# ノードを描画
nx.draw_networkx_nodes(graph, pos, node_size=30, node_color='lightblue', alpha=0.8)

# エッジタイプごとに描画
for edge_type, color in edge_colors.items():
    edges = [(u, v) for u, v, d in graph.edges(data=True) if d.get('edge_type') == edge_type]
    nx.draw_networkx_edges(graph, pos, edgelist=edges, edge_color=color,
                           width=1.5, alpha=0.6, label=edge_type)

plt.legend()
plt.axis('off')
plt.tight_layout()
plt.savefig('graph_by_edge_type.png', dpi=300, bbox_inches='tight')
plt.show()
```

**ワールド座標で可視化:**
```python
import networkx as nx
import matplotlib.pyplot as plt

graph = nx.read_gml('output/graph.gml')

# ワールド座標を位置として使用
pos = {}
for node, data in graph.nodes(data=True):
    world = data['world']
    pos[node] = (world[0], world[1])  # x, y座標

plt.figure(figsize=(15, 10))
nx.draw_networkx_nodes(graph, pos, node_size=30, node_color='red', alpha=0.8)
nx.draw_networkx_edges(graph, pos, alpha=0.5, width=1)
plt.axis('equal')
plt.grid(True, alpha=0.3)
plt.xlabel('X (meters)')
plt.ylabel('Y (meters)')
plt.title('SWAGGER Graph - World Coordinates')
plt.tight_layout()
plt.savefig('graph_world_coordinates.png', dpi=300, bbox_inches='tight')
plt.show()
```

**元の地図に重ねて表示:**
```python
import networkx as nx
import matplotlib.pyplot as plt
import cv2

# 地図を読み込み
map_image = cv2.imread('maps/carter_warehouse_navigation.png', cv2.IMREAD_GRAYSCALE)
map_image = cv2.cvtColor(map_image, cv2.COLOR_GRAY2RGB)

# グラフを読み込み
graph = nx.read_gml('output/graph.gml')

# ピクセル座標を位置として使用
pos = {}
for node, data in graph.nodes(data=True):
    pixel = data['pixel']
    pos[node] = (pixel[1], pixel[0])  # x=col, y=row

# 描画
fig, ax = plt.subplots(figsize=(15, 10))
ax.imshow(map_image, cmap='gray', origin='upper')

# エッジを描画
for u, v in graph.edges():
    x = [pos[u][0], pos[v][0]]
    y = [pos[u][1], pos[v][1]]
    ax.plot(x, y, 'r-', linewidth=0.5, alpha=0.6)

# ノードを描画
for node in graph.nodes():
    ax.plot(pos[node][0], pos[node][1], 'bo', markersize=2)

ax.axis('off')
plt.tight_layout()
plt.savefig('graph_on_map.png', dpi=300, bbox_inches='tight')
plt.show()
```

---

### 2. Plotly（インタラクティブ）⭐

**インストール:**
```bash
pip install plotly networkx
```

**インタラクティブな可視化:**
```python
import networkx as nx
import plotly.graph_objects as go

# GMLファイルを読み込み
graph = nx.read_gml('output/graph.gml')

# レイアウト計算
pos = nx.spring_layout(graph, k=0.5, iterations=50)

# エッジの座標
edge_x = []
edge_y = []
for edge in graph.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=0.5, color='#888'),
    hoverinfo='none',
    mode='lines')

# ノードの座標
node_x = []
node_y = []
node_text = []
for node, data in graph.nodes(data=True):
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    node_text.append(f"Node {node}<br>World: {data.get('world', 'N/A')}")

node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode='markers',
    hoverinfo='text',
    text=node_text,
    marker=dict(
        showscale=True,
        colorscale='YlGnBu',
        size=10,
        colorbar=dict(
            thickness=15,
            title='Node Connections',
            xanchor='left',
            titleside='right'
        ),
        line_width=2))

# ノードの次数で色付け
node_adjacencies = []
for node, adjacencies in enumerate(graph.adjacency()):
    node_adjacencies.append(len(adjacencies[1]))
node_trace.marker.color = node_adjacencies

# 図を作成
fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    title='SWAGGER Graph - Interactive Visualization',
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=0, l=0, r=0, t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                )

# HTML形式で保存
fig.write_html("graph_interactive.html")
fig.show()
```

**機能:**
- ズーム・パン可能
- ノードにマウスオーバーで情報表示
- ブラウザで開ける

---

### 3. igraph

**インストール:**
```bash
pip install igraph cairocffi
```

**高速な可視化:**
```python
import igraph as ig

# GMLファイルを読み込み
graph = ig.Graph.Read_GML('output/graph.gml')

# 可視化設定
visual_style = {
    "vertex_size": 5,
    "vertex_color": "lightblue",
    "edge_width": 0.5,
    "edge_color": "gray",
    "layout": graph.layout("fr"),  # Fruchterman-Reingold
    "bbox": (800, 600),
    "margin": 50
}

# PNG形式で保存
ig.plot(graph, "graph_igraph.png", **visual_style)
```

---

## Webベースツール

### 1. Vis.js

**特徴:**
- ブラウザで動作
- インタラクティブ
- リアルタイム更新可能

**GMLからJSONへ変換:**
```python
import networkx as nx
import json

graph = nx.read_gml('output/graph.gml')

# Vis.js形式に変換
vis_data = {
    "nodes": [
        {"id": node, "label": str(node), "x": data['world'][0], "y": data['world'][1]}
        for node, data in graph.nodes(data=True)
    ],
    "edges": [
        {"from": u, "to": v, "value": data.get('weight', 1)}
        for u, v, data in graph.edges(data=True)
    ]
}

with open('graph_vis.json', 'w') as f:
    json.dump(vis_data, f, indent=2)
```

**HTML:**
```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        #mynetwork {
            width: 100%;
            height: 600px;
            border: 1px solid lightgray;
        }
    </style>
</head>
<body>
    <div id="mynetwork"></div>
    <script>
        fetch('graph_vis.json')
            .then(response => response.json())
            .then(data => {
                var container = document.getElementById('mynetwork');
                var options = {
                    physics: {
                        enabled: true,
                        stabilization: { iterations: 100 }
                    }
                };
                var network = new vis.Network(container, data, options);
            });
    </script>
</body>
</html>
```

---

### 2. D3.js

**特徴:**
- 最も柔軟なWeb可視化ライブラリ
- カスタマイズ性が高い
- アニメーション対応

**GMLからJSONへ変換:**
```python
import networkx as nx
import json

graph = nx.read_gml('output/graph.gml')

d3_data = {
    "nodes": [
        {"id": str(node), "group": 1, **data}
        for node, data in graph.nodes(data=True)
    ],
    "links": [
        {"source": str(u), "target": str(v), "value": data.get('weight', 1)}
        for u, v, data in graph.edges(data=True)
    ]
}

with open('graph_d3.json', 'w') as f:
    json.dump(d3_data, f, indent=2)
```

---

## コマンドラインツール

### Graphviz

**インストール:**
```bash
sudo apt install graphviz
```

**GMLから変換して可視化:**
```python
import networkx as nx

# GMLを読み込み
graph = nx.read_gml('output/graph.gml')

# DOT形式に変換
nx.drawing.nx_pydot.write_dot(graph, 'graph.dot')
```

```bash
# PNG形式で出力
dot -Tpng graph.dot -o graph_graphviz.png

# SVG形式で出力
dot -Tsvg graph.dot -o graph_graphviz.svg

# PDF形式で出力
dot -Tpdf graph.dot -o graph_graphviz.pdf
```

**レイアウトオプション:**
```bash
# Different layout engines
dot -Tpng graph.dot -o graph_dot.png      # 階層的
neato -Tpng graph.dot -o graph_neato.png  # Spring
fdp -Tpng graph.dot -o graph_fdp.png      # Force-directed
sfdp -Tpng graph.dot -o graph_sfdp.png    # Scalable force-directed
circo -Tpng graph.dot -o graph_circo.png  # 円形
```

---

## 推奨ツール比較

| ツール | 難易度 | 速度 | 機能性 | 用途 |
|--------|--------|------|--------|------|
| **Gephi** | 低 | 高 | ⭐⭐⭐⭐⭐ | 大規模グラフ、論文用 |
| **NetworkX + Matplotlib** | 中 | 中 | ⭐⭐⭐ | Python環境、カスタマイズ |
| **Plotly** | 中 | 中 | ⭐⭐⭐⭐ | インタラクティブ、Web |
| **yEd** | 低 | 高 | ⭐⭐⭐⭐ | きれいなレイアウト |
| **Cytoscape** | 中 | 中 | ⭐⭐⭐⭐ | 分析機能重視 |
| **Graphviz** | 低 | 高 | ⭐⭐⭐ | コマンドライン、自動化 |
| **Vis.js** | 高 | 中 | ⭐⭐⭐⭐ | Webアプリ組み込み |
| **D3.js** | 高 | 中 | ⭐⭐⭐⭐⭐ | 完全カスタマイズ |

---

## 用途別推奨

### 論文・プレゼンテーション用
→ **Gephi** または **yEd**
- 高品質な画像出力
- 美しいレイアウト

### Pythonでの分析と可視化
→ **NetworkX + Matplotlib** または **Plotly**
- コード内で完結
- カスタマイズ容易

### Webアプリケーション
→ **Vis.js** または **D3.js**
- ブラウザで動作
- インタラクティブ

### 大規模グラフ（10万ノード以上）
→ **Gephi** または **igraph**
- 高速処理
- メモリ効率良好

### クイックチェック
→ **NetworkX + Matplotlib**
- 最も手軽
- すぐに確認可能

---

## 実践例：SWAGGERグラフの可視化

### 完全な可視化スクリプト

```python
#!/usr/bin/env python3
"""SWAGGER GMLグラフの可視化スクリプト"""

import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

def visualize_swagger_graph(gml_path, map_path=None, output_path='swagger_graph_viz.png'):
    """SWAGGERグラフを可視化

    Args:
        gml_path: GMLファイルのパス
        map_path: 元の地図画像のパス（オプション）
        output_path: 出力画像のパス
    """
    # グラフを読み込み
    graph = nx.read_gml(gml_path)
    print(f"Loaded graph: {len(graph.nodes())} nodes, {len(graph.edges())} edges")

    # エッジタイプごとの色とラベル
    edge_styles = {
        'skeleton': {'color': 'red', 'alpha': 0.8, 'width': 1.5, 'label': 'Skeleton'},
        'boundary': {'color': 'blue', 'alpha': 0.7, 'width': 1.2, 'label': 'Boundary'},
        'delaunay': {'color': 'green', 'alpha': 0.5, 'width': 0.8, 'label': 'Delaunay'},
        'merge': {'color': 'orange', 'alpha': 0.6, 'width': 1.0, 'label': 'Merge'},
        'contour': {'color': 'purple', 'alpha': 0.7, 'width': 1.2, 'label': 'Contour'},
        'grid': {'color': 'gray', 'alpha': 0.5, 'width': 0.5, 'label': 'Grid'}
    }

    # ピクセル座標を位置として使用
    pos = {}
    for node, data in graph.nodes(data=True):
        pixel = data.get('pixel', [0, 0])
        pos[node] = (pixel[1], pixel[0])  # (x, y) = (col, row)

    # 図を作成
    fig, ax = plt.subplots(figsize=(20, 15))

    # 元の地図を背景に表示（オプション）
    if map_path:
        import cv2
        map_image = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
        ax.imshow(map_image, cmap='gray', alpha=0.3, origin='upper')

    # エッジタイプごとに描画
    legend_handles = []
    for edge_type, style in edge_styles.items():
        edges = [(u, v) for u, v, d in graph.edges(data=True)
                 if d.get('edge_type') == edge_type]
        if edges:
            nx.draw_networkx_edges(
                graph, pos, edgelist=edges,
                edge_color=style['color'],
                alpha=style['alpha'],
                width=style['width'],
                ax=ax
            )
            # 凡例用
            legend_handles.append(plt.Line2D([0], [0], color=style['color'],
                                            linewidth=style['width'],
                                            label=f"{style['label']} ({len(edges)})"))

    # ノードを描画
    nx.draw_networkx_nodes(
        graph, pos,
        node_size=20,
        node_color='darkblue',
        alpha=0.6,
        ax=ax
    )

    # 統計情報を表示
    stats_text = (
        f"Nodes: {len(graph.nodes())}\n"
        f"Edges: {len(graph.edges())}\n"
        f"Connected: {nx.is_connected(graph)}\n"
        f"Components: {nx.number_connected_components(graph)}"
    )
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    # 凡例
    ax.legend(handles=legend_handles, loc='upper right', fontsize=10)

    ax.set_title('SWAGGER Waypoint Graph Visualization', fontsize=16, fontweight='bold')
    ax.axis('equal')
    ax.axis('off')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Saved visualization to {output_path}")
    plt.close()

    # グラフ統計を出力
    print("\nGraph Statistics:")
    print(f"  Nodes: {len(graph.nodes())}")
    print(f"  Edges: {len(graph.edges())}")
    print(f"  Average degree: {sum(dict(graph.degree()).values()) / len(graph.nodes()):.2f}")
    print(f"  Is connected: {nx.is_connected(graph)}")
    print(f"  Number of components: {nx.number_connected_components(graph)}")

    # エッジタイプ別統計
    print("\nEdge Types:")
    edge_type_counts = {}
    for u, v, data in graph.edges(data=True):
        edge_type = data.get('edge_type', 'unknown')
        edge_type_counts[edge_type] = edge_type_counts.get(edge_type, 0) + 1
    for edge_type, count in sorted(edge_type_counts.items()):
        print(f"  {edge_type}: {count}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python visualize_swagger_graph.py <gml_file> [map_image] [output_image]")
        sys.exit(1)

    gml_path = sys.argv[1]
    map_path = sys.argv[2] if len(sys.argv) > 2 else None
    output_path = sys.argv[3] if len(sys.argv) > 3 else 'swagger_graph_viz.png'

    visualize_swagger_graph(gml_path, map_path, output_path)
```

**使い方:**
```bash
python visualize_swagger_graph.py output/graph.gml maps/warehouse.png output/viz.png
```

---

## まとめ

**初心者には:**
- Gephi（GUI、簡単）
- NetworkX + Matplotlib（Python、標準的）

**開発者には:**
- NetworkX + Plotly（インタラクティブ）
- Vis.js/D3.js（Web統合）

**研究者には:**
- Gephi（論文用の高品質画像）
- Cytoscape（詳細分析）

**大規模グラフには:**
- Gephi（最も高速）
- igraph（プログラマティック）

すべてのツールがGML形式に対応しているので、用途に応じて選択できます！
