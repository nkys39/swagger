#!/usr/bin/env python3
"""グラフの読み込みと利用例"""

import pickle
import networkx as nx


def main():
    # グラフを読み込み
    print("グラフを読み込んでいます...")
    with open('output/graph.pkl', 'rb') as f:
        graph = pickle.load(f)

    # 基本情報
    print("\n=== グラフの基本情報 ===")
    print(f"ノード数: {len(graph.nodes)}")
    print(f"エッジ数: {len(graph.edges)}")
    print(f"連結成分数: {nx.number_connected_components(graph)}")

    # ノードの次数
    degrees = [graph.degree(n) for n in graph.nodes()]
    print(f"\n最小次数: {min(degrees)}")
    print(f"最大次数: {max(degrees)}")
    print(f"平均次数: {sum(degrees) / len(degrees):.2f}")

    # ノードタイプの統計
    node_types = {}
    for node, data in graph.nodes(data=True):
        node_type = data.get('node_type', 'unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1

    print("\n=== ノードタイプ ===")
    for node_type, count in sorted(node_types.items()):
        print(f"{node_type}: {count}個")

    # エッジタイプの統計
    edge_types = {}
    total_weight = 0
    for src, dst, data in graph.edges(data=True):
        edge_type = data.get('edge_type', 'unknown')
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
        total_weight += data.get('weight', 0)

    print("\n=== エッジタイプ ===")
    for edge_type, count in sorted(edge_types.items()):
        print(f"{edge_type}: {count}個")

    print(f"\nエッジの総長: {total_weight:.2f}ピクセル")

    # サンプルノードを表示
    print("\n=== サンプルノード（最初の5個） ===")
    for i, (node, data) in enumerate(list(graph.nodes(data=True))[:5]):
        row, col = node
        node_type = data.get('node_type', 'unknown')
        print(f"ノード{i+1}: 座標=({row}, {col}), タイプ={node_type}")

    # サンプルエッジを表示
    print("\n=== サンプルエッジ（最初の5個） ===")
    for i, (src, dst, data) in enumerate(list(graph.edges(data=True))[:5]):
        weight = data.get('weight', 0)
        edge_type = data.get('edge_type', 'unknown')
        print(f"エッジ{i+1}: {src} -> {dst}, 重み={weight:.2f}px, タイプ={edge_type}")

    # 最短経路の例
    nodes = list(graph.nodes())
    if len(nodes) >= 2:
        start = nodes[0]
        goal = nodes[len(nodes)//2]  # 中間のノードを選択

        print(f"\n=== 最短経路の例 ===")
        print(f"開始: {start}")
        print(f"目標: {goal}")

        try:
            path = nx.shortest_path(graph, start, goal, weight='weight')
            path_length = nx.shortest_path_length(graph, start, goal, weight='weight')
            print(f"最短経路: {len(path)}ノード")
            print(f"経路長: {path_length:.2f}ピクセル")
            print(f"経路（最初の5ノード）: {path[:5]}")
        except nx.NetworkXNoPath:
            print("経路が見つかりませんでした（ノードが異なる連結成分にあります）")

    print("\n処理完了！")


if __name__ == "__main__":
    main()
