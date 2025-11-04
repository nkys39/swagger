#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
SWAGGER Minimal: Step1 (Preprocess) + Step3 (Boundary Sampling)

このスクリプトは以下の処理を行います：
1. Step1: 占有グリッドマップの前処理と距離変換
2. Step3: 障害物境界のサンプリングによるノード配置とエッジ接続

使用方法:
    python process_map.py --map <マップファイル> --output <出力ディレクトリ>
"""

import argparse
import logging
import os
import pickle
from pathlib import Path
from typing import Optional

import cv2
import networkx as nx
import numpy as np


# ============================================================================
# ロガー設定
# ============================================================================

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """ロガーをセットアップする。

    Args:
        name: ロガー名
        level: ログレベル (DEBUG, INFO, WARNING, ERROR)

    Returns:
        設定済みのロガー
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }

    logger = logging.getLogger(name)
    logger.setLevel(level_map.get(level, logging.INFO))

    # ハンドラが既に存在する場合はスキップ
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# ============================================================================
# Step 1: 前処理と距離変換
# ============================================================================

def load_map(map_path: str) -> np.ndarray:
    """占有グリッドマップを読み込む。

    Args:
        map_path: マップ画像ファイルのパス

    Returns:
        占有グリッド（numpy配列）
    """
    if not os.path.exists(map_path):
        raise FileNotFoundError(f"マップファイルが見つかりません: {map_path}")

    occupancy_grid = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)
    if occupancy_grid is None:
        raise ValueError(f"マップの読み込みに失敗しました: {map_path}")

    return occupancy_grid


def distance_transform(
    free_map: np.ndarray,
    resolution: float,
    safety_distance: float,
    logger: logging.Logger
) -> tuple[np.ndarray, np.ndarray]:
    """距離変換を計算し、障害物を膨張させる。

    Args:
        free_map: 二値マップ（1=自由空間, 0=占有）
        resolution: マップの解像度（メートル/ピクセル）
        safety_distance: ロボットの半径（メートル）
        logger: ロガーインスタンス

    Returns:
        (距離変換マップ, 膨張障害物マップ) のタプル
    """
    logger.info("距離変換を計算中...")

    # マップを1ピクセルずつパディング
    free_map_padded = np.pad(free_map, ((1, 1), (1, 1)), mode="constant", constant_values=0)

    # 距離変換を計算
    dist_transform = cv2.distanceTransform(free_map_padded, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)

    # ロボットの半径でフィルタリングして膨張マップを作成
    inflated_map = (dist_transform < safety_distance / resolution).astype(np.uint8)

    # パディングを除去
    dist_transform = dist_transform[1:-1, 1:-1]
    inflated_map = inflated_map[1:-1, 1:-1]

    logger.info("距離変換完了")
    return dist_transform, inflated_map


def step1_preprocess(
    map_path: str,
    resolution: float,
    safety_distance: float,
    occupancy_threshold: int,
    logger: logging.Logger
) -> dict:
    """Step 1: マップの前処理を実行する。

    Args:
        map_path: マップファイルのパス
        resolution: 解像度（m/px）
        safety_distance: 安全距離（m）
        occupancy_threshold: 占有閾値（0-255）
        logger: ロガー

    Returns:
        前処理データの辞書
    """
    logger.info("=" * 60)
    logger.info("Step 1: 前処理")
    logger.info("=" * 60)

    # マップを読み込み
    logger.info(f"マップを読み込み中: {map_path}")
    original_map = load_map(map_path)
    logger.info(f"マップサイズ: {original_map.shape}")

    # パラメータをログ出力
    logger.info(f"パラメータ:")
    logger.info(f"  解像度: {resolution} m/px")
    logger.info(f"  安全距離: {safety_distance} m")
    logger.info(f"  占有閾値: {occupancy_threshold}")

    # 自由空間マップを作成
    free_map = (original_map > occupancy_threshold).astype(np.uint8)
    free_pixels = np.sum(free_map)
    total_pixels = free_map.size
    free_percentage = (free_pixels / total_pixels) * 100
    logger.info(f"自由空間: {free_pixels}/{total_pixels} ピクセル ({free_percentage:.1f}%)")

    # マップが完全に自由空間かチェック
    if np.all(free_map):
        logger.warning("マップは完全に自由空間です - 障害物が検出されませんでした！")
        logger.info("距離変換をスキップ")
        dist_transform = None
        inflated_map = np.zeros_like(free_map)
    else:
        # 距離変換を計算
        dist_transform, inflated_map = distance_transform(
            free_map,
            resolution,
            safety_distance,
            logger
        )

    logger.info("Step 1 完了！")

    return {
        "original_map": original_map,
        "free_map": free_map,
        "dist_transform": dist_transform,
        "inflated_map": inflated_map,
        "resolution": resolution,
        "safety_distance": safety_distance,
        "occupancy_threshold": occupancy_threshold,
    }


# ============================================================================
# Step 3: 障害物境界サンプリング
# ============================================================================

def check_line_collision(p0: tuple, p1: tuple, inflated_map: np.ndarray) -> bool:
    """2点間の線分が障害物と交差するかチェックする（Bresenhamアルゴリズム）。

    Args:
        p0: 開始点の座標（row, col）
        p1: 終了点の座標（row, col）
        inflated_map: 二値障害物マップ

    Returns:
        衝突がある場合True
    """
    y0, x0 = p0
    y1, x1 = p1
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    while True:
        if inflated_map[y0, x0]:
            return True
        if (y0 == y1) and (x0 == x1):
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

    return False


def find_obstacle_contours(
    dist_transform: np.ndarray,
    boundary_inflation: float
) -> list:
    """膨張した障害物の輪郭を検出する。

    Args:
        dist_transform: 自由空間の距離変換
        boundary_inflation: 膨張距離（ピクセル）

    Returns:
        輪郭のリスト
    """
    filtered_obstacles = (dist_transform >= boundary_inflation).astype(np.uint8)
    contours, _ = cv2.findContours(
        filtered_obstacles,
        cv2.RETR_LIST,
        cv2.CHAIN_APPROX_TC89_KCOS
    )
    return contours


def connect_contour_nodes(
    contour_nodes: list,
    graph: nx.Graph,
    inflated_map: np.ndarray
) -> None:
    """輪郭に沿って連続するノードを接続する。

    Args:
        contour_nodes: 輪郭上のノード座標のリスト
        graph: エッジを追加するNetworkXグラフ
        inflated_map: 衝突チェック用の二値障害物マップ
    """
    for i in range(len(contour_nodes)):
        n1 = contour_nodes[i]
        n2 = contour_nodes[(i + 1) % len(contour_nodes)]

        if not check_line_collision(n1, n2, inflated_map):
            dist = np.sqrt((n1[0] - n2[0]) ** 2 + (n1[1] - n2[1]) ** 2)
            graph.add_edge(n1, n2, weight=dist, edge_type="contour")


def sample_obstacle_boundaries(
    graph: nx.Graph,
    dist_transform: np.ndarray,
    inflated_map: np.ndarray,
    boundary_inflation_px: float,
    sample_distance_px: int,
    logger: logging.Logger
) -> int:
    """障害物境界に沿ってノードをサンプリングする。

    Args:
        graph: 境界ノードを追加する既存のグラフ
        dist_transform: 距離変換
        inflated_map: 二値膨張障害物マップ
        boundary_inflation_px: 境界膨張（ピクセル）
        sample_distance_px: サンプル間の距離（ピクセル）
        logger: ロガーインスタンス

    Returns:
        追加されたノード数
    """
    logger.info(f"障害物輪郭を検出中（膨張: {boundary_inflation_px:.1f}px）...")
    contours = find_obstacle_contours(dist_transform, boundary_inflation_px)
    logger.info(f"{len(contours)}個の輪郭を検出しました")

    initial_num_nodes = len(graph.nodes())

    for contour_idx, contour in enumerate(contours):
        contour_nodes = []

        # 輪郭の各頂点を処理
        for i in range(len(contour)):
            p1 = contour[i][0]
            p2 = contour[(i + 1) % len(contour)][0]

            # 最初の頂点を追加
            row_1, col_1 = int(p1[1]), int(p1[0])
            contour_nodes.append((row_1, col_1))
            graph.add_node((row_1, col_1), node_type="boundary")

            # 次の頂点までの距離を計算
            segment_length = np.linalg.norm(p2 - p1)

            # 中間点を追加
            num_intermediate = int(segment_length / sample_distance_px)
            intermediate_points = np.linspace(
                p1, p2,
                num=num_intermediate,
                endpoint=False
            ).astype(int).tolist()[1:]

            for point in intermediate_points:
                col, row = point
                contour_nodes.append((row, col))
                graph.add_node((row, col), node_type="boundary")

        # この輪郭に沿ってノードを接続
        connect_contour_nodes(contour_nodes, graph, inflated_map)

    num_nodes_added = len(graph.nodes()) - initial_num_nodes
    logger.info(f"{num_nodes_added}個の境界ノードを追加しました")
    return num_nodes_added


def step3_boundary_sampling(
    step1_data: dict,
    boundary_inflation_factor: float,
    boundary_sample_distance: float,
    logger: logging.Logger
) -> nx.Graph:
    """Step 3: 障害物境界サンプリングを実行する。

    Args:
        step1_data: Step 1の出力データ
        boundary_inflation_factor: 境界膨張係数
        boundary_sample_distance: サンプリング距離（メートル）
        logger: ロガー

    Returns:
        ノードとエッジを含むグラフ
    """
    logger.info("=" * 60)
    logger.info("Step 3: 障害物境界サンプリング")
    logger.info("=" * 60)

    # 新しいグラフを作成
    graph = nx.Graph()

    # パラメータをピクセルに変換
    resolution = step1_data["resolution"]
    safety_distance = step1_data["safety_distance"]
    boundary_inflation_px = boundary_inflation_factor * safety_distance / resolution
    sample_distance_px = int(boundary_sample_distance / resolution)

    logger.info(f"境界膨張: {boundary_inflation_factor} * {safety_distance}m = {boundary_inflation_px:.1f}px")
    logger.info(f"サンプル距離: {boundary_sample_distance}m = {sample_distance_px}px")

    # 境界をサンプリング
    if step1_data["dist_transform"] is not None:
        sample_obstacle_boundaries(
            graph,
            step1_data["dist_transform"],
            step1_data["inflated_map"],
            boundary_inflation_px,
            sample_distance_px,
            logger
        )
    else:
        logger.warning("距離変換がありません - 境界サンプリングをスキップします")

    logger.info(f"合計グラフ: {len(graph.nodes)}個のノード, {len(graph.edges)}個のエッジ")
    logger.info("Step 3 完了！")

    return graph


# ============================================================================
# 可視化
# ============================================================================

def visualize_graph(
    graph: nx.Graph,
    original_map: np.ndarray,
    output_path: str,
    logger: logging.Logger
) -> None:
    """グラフを元のマップ上に可視化する。

    Args:
        graph: NetworkXグラフ
        original_map: 元の占有グリッド
        output_path: 保存先パス
        logger: ロガー
    """
    logger.info("グラフを可視化中...")

    # BGRに変換
    map_vis = cv2.cvtColor(original_map, cv2.COLOR_GRAY2BGR)

    # エッジを描画（青色）
    edge_color = (255, 0, 0)  # BGR: 青
    for src, dst in graph.edges():
        y1, x1 = src
        y2, x2 = dst
        cv2.line(map_vis, (x1, y1), (x2, y2), edge_color, 1)

    # ノードを描画（赤色）
    node_radius = 2
    node_color = (0, 0, 255)  # BGR: 赤
    for node in graph.nodes():
        y, x = node
        cv2.circle(map_vis, (x, y), node_radius, node_color, -1)

    # 保存
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    if not cv2.imwrite(output_path, map_vis):
        raise RuntimeError(f"可視化の保存に失敗しました: {output_path}")

    logger.info(f"可視化を保存しました: {output_path}")


def save_results(
    step1_data: dict,
    graph: nx.Graph,
    output_dir: str,
    logger: logging.Logger,
    save_gml: bool = False,
    save_graphml: bool = False
) -> None:
    """結果を保存する。

    Args:
        step1_data: Step 1のデータ
        graph: 生成されたグラフ
        output_dir: 出力ディレクトリ
        logger: ロガー
        save_gml: GML形式で保存するか
        save_graphml: GraphML形式で保存するか
    """
    os.makedirs(output_dir, exist_ok=True)

    # グラフをPickle形式で保存
    graph_path = os.path.join(output_dir, "graph.pkl")
    with open(graph_path, 'wb') as f:
        pickle.dump(graph, f)
    logger.info(f"グラフを保存しました: {graph_path}")

    # GML形式で保存
    if save_gml:
        gml_path = os.path.join(output_dir, "graph.gml")
        try:
            nx.write_gml(graph, gml_path)
            logger.info(f"GML形式で保存しました: {gml_path}")
        except Exception as e:
            logger.error(f"GML保存エラー: {e}")

    # GraphML形式で保存
    if save_graphml:
        graphml_path = os.path.join(output_dir, "graph.graphml")
        try:
            nx.write_graphml(graph, graphml_path)
            logger.info(f"GraphML形式で保存しました: {graphml_path}")
        except Exception as e:
            logger.error(f"GraphML保存エラー: {e}")

    # ノード座標をテキスト形式で保存
    nodes_path = os.path.join(output_dir, "nodes.txt")
    with open(nodes_path, 'w') as f:
        f.write("# row, col (pixel coordinates)\n")
        for node in sorted(graph.nodes()):
            row, col = node
            f.write(f"{row}, {col}\n")
    logger.info(f"ノード座標を保存しました: {nodes_path}")

    # エッジをテキスト形式で保存
    edges_path = os.path.join(output_dir, "edges.txt")
    with open(edges_path, 'w') as f:
        f.write("# src_row, src_col, dst_row, dst_col, weight, edge_type\n")
        for src, dst, data in graph.edges(data=True):
            src_row, src_col = src
            dst_row, dst_col = dst
            weight = data.get('weight', 0.0)
            edge_type = data.get('edge_type', 'unknown')
            f.write(f"{src_row}, {src_col}, {dst_row}, {dst_col}, {weight:.3f}, {edge_type}\n")
    logger.info(f"エッジ情報を保存しました: {edges_path}")

    # 可視化を保存
    vis_path = os.path.join(output_dir, "graph_visualization.png")
    visualize_graph(graph, step1_data["original_map"], vis_path, logger)


# ============================================================================
# メイン処理
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="SWAGGER Minimal: マップ前処理 + 障害物境界サンプリング"
    )

    # 必須引数
    parser.add_argument(
        "--map",
        type=str,
        required=True,
        help="占有グリッドマップのパス（PNG/PGM形式）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="output",
        help="出力ディレクトリ（デフォルト: output）"
    )

    # マップパラメータ
    parser.add_argument(
        "--resolution",
        type=float,
        default=0.05,
        help="マップ解像度（メートル/ピクセル、デフォルト: 0.05）"
    )
    parser.add_argument(
        "--safety-distance",
        type=float,
        default=0.5,
        help="ロボット半径（メートル、デフォルト: 0.5）"
    )
    parser.add_argument(
        "--occupancy-threshold",
        type=int,
        default=127,
        help="占有閾値（0-255、デフォルト: 127）"
    )

    # Step 3パラメータ
    parser.add_argument(
        "--boundary-inflation-factor",
        type=float,
        default=1.5,
        help="境界膨張係数（デフォルト: 1.5）"
    )
    parser.add_argument(
        "--boundary-sample-distance",
        type=float,
        default=2.5,
        help="輪郭に沿ったサンプリング距離（メートル、デフォルト: 2.5）"
    )

    # 出力形式
    parser.add_argument(
        "--save-gml",
        action="store_true",
        help="GML形式でグラフを保存する"
    )
    parser.add_argument(
        "--save-graphml",
        action="store_true",
        help="GraphML形式でグラフを保存する"
    )

    # その他
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="ログレベル（デフォルト: INFO）"
    )

    args = parser.parse_args()

    # ロガーをセットアップ
    logger = setup_logger(__name__, args.log_level)

    logger.info("=" * 60)
    logger.info("SWAGGER Minimal: Step1 + Step3")
    logger.info("=" * 60)

    # Step 1: 前処理
    step1_data = step1_preprocess(
        map_path=args.map,
        resolution=args.resolution,
        safety_distance=args.safety_distance,
        occupancy_threshold=args.occupancy_threshold,
        logger=logger
    )

    # Step 3: 障害物境界サンプリング
    graph = step3_boundary_sampling(
        step1_data=step1_data,
        boundary_inflation_factor=args.boundary_inflation_factor,
        boundary_sample_distance=args.boundary_sample_distance,
        logger=logger
    )

    # 結果を保存
    save_results(
        step1_data,
        graph,
        args.output,
        logger,
        save_gml=args.save_gml,
        save_graphml=args.save_graphml
    )

    logger.info("=" * 60)
    logger.info("全処理完了！")
    logger.info(f"結果は {args.output} ディレクトリに保存されました")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
