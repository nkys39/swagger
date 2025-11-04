#!/usr/bin/env python3
"""GML/GraphMLファイルの読み込みテスト"""

import networkx as nx


def test_gml():
    print("=== GML形式の読み込みテスト ===")

    # GMLから読み込み
    graph = nx.read_gml('output_test/graph.gml')
    print(f"ノード数: {len(graph.nodes)}")
    print(f"エッジ数: {len(graph.edges)}")

    # ノード属性を確認
    print("\nサンプルノード（最初の3個）:")
    for i, (node, data) in enumerate(list(graph.nodes(data=True))[:3]):
        print(f"  {i+1}. ID={node}, node_type={data.get('node_type', 'N/A')}")

    # エッジ属性を確認
    print("\nサンプルエッジ（最初の3個）:")
    for i, (src, dst, data) in enumerate(list(graph.edges(data=True))[:3]):
        weight = data.get('weight', 0)
        edge_type = data.get('edge_type', 'N/A')
        print(f"  {i+1}. {src} -> {dst}, weight={weight:.2f}, type={edge_type}")


def test_graphml():
    print("\n=== GraphML形式の読み込みテスト ===")

    # GraphMLから読み込み
    graph = nx.read_graphml('output_test/graph.graphml')
    print(f"ノード数: {len(graph.nodes)}")
    print(f"エッジ数: {len(graph.edges)}")

    # ノード属性を確認
    print("\nサンプルノード（最初の3個）:")
    for i, (node, data) in enumerate(list(graph.nodes(data=True))[:3]):
        print(f"  {i+1}. ID={node}, node_type={data.get('node_type', 'N/A')}")

    # エッジ属性を確認
    print("\nサンプルエッジ（最初の3個）:")
    for i, (src, dst, data) in enumerate(list(graph.edges(data=True))[:3]):
        weight = data.get('weight', 0)
        edge_type = data.get('edge_type', 'N/A')
        print(f"  {i+1}. {src} -> {dst}, weight={weight:.2f}, type={edge_type}")


if __name__ == "__main__":
    test_gml()
    test_graphml()
    print("\n✓ すべてのテスト完了！")
