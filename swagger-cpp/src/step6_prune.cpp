#include "step6_prune.hpp"
#include "utils.hpp"
#include <iostream>
#include <cmath>
#include <set>
#include <vector>
#include <opencv2/flann.hpp>

namespace swagger {

void GraphPruner::log(const std::string& message, bool verbose) {
    if (verbose) {
        std::cout << message << std::endl;
    }
}

bool GraphPruner::check_line_collision(
    const cv::Point& p0,
    const cv::Point& p1,
    const cv::Mat& inflated_map
) {
    // Bresenham's line algorithm
    int x0 = p0.x;
    int y0 = p0.y;
    int x1 = p1.x;
    int y1 = p1.y;

    int dx = std::abs(x1 - x0);
    int dy = std::abs(y1 - y0);
    int sx = (x0 < x1) ? 1 : -1;
    int sy = (y0 < y1) ? 1 : -1;
    int err = dx - dy;

    while (true) {
        // Check bounds
        if (y0 < 0 || y0 >= inflated_map.rows || x0 < 0 || x0 >= inflated_map.cols) {
            return true;
        }

        // Check collision
        if (inflated_map.at<uchar>(y0, x0) > 0) {
            return true;
        }

        // Check if reached end
        if (x0 == x1 && y0 == y1) {
            break;
        }

        int e2 = 2 * err;
        if (e2 > -dy) {
            err -= dy;
            x0 += sx;
        }
        if (e2 < dx) {
            err += dx;
            y0 += sy;
        }
    }

    return false;
}

size_t GraphPruner::merge_close_nodes(
    Graph& graph,
    const cv::Mat& inflated_map,
    double merge_distance_px,
    bool verbose
) {
    size_t initial_num_nodes = graph.num_nodes();
    int iteration = 0;
    int max_iterations = 50;

    while (iteration < max_iterations) {
        iteration++;

        auto nodes = graph.nodes();
        if (nodes.empty()) {
            break;
        }

        if (verbose) {
            log("統合反復 " + std::to_string(iteration) + ": " + std::to_string(nodes.size()) + "個のノードを処理中...", verbose);
        }

        bool merged = false;

        // Build KD-tree for efficient proximity search
        if (verbose) {
            log("  KD-treeを構築中...", verbose);
        }

        cv::Mat node_coords(nodes.size(), 2, CV_32F);
        for (size_t i = 0; i < nodes.size(); ++i) {
            node_coords.at<float>(i, 0) = static_cast<float>(nodes[i].second);  // x (col)
            node_coords.at<float>(i, 1) = static_cast<float>(nodes[i].first);   // y (row)
        }

        cv::flann::Index kdtree(node_coords, cv::flann::KDTreeIndexParams(1), cvflann::FLANN_DIST_EUCLIDEAN);

        if (verbose) {
            log("  KD-tree構築完了", verbose);
        }

        // Find close node pairs using KD-tree
        std::set<std::pair<size_t, size_t>> close_pairs;

        if (verbose) {
            log("  KD-treeで近接ペアを探索中...", verbose);
        }

        for (size_t i = 0; i < nodes.size(); ++i) {
            if (verbose && i % 100 == 0) {
                log("  KD-tree探索: " + std::to_string(i) + "/" + std::to_string(nodes.size()) + " ノード", verbose);
            }

            if (verbose && i < 5) {
                log("  ノード " + std::to_string(i) + " の近接探索を開始", verbose);
            }

            if (!graph.has_node(nodes[i])) {
                continue;  // Already removed
            }

            // Query for all neighbors within merge distance
            cv::Mat query(1, 2, CV_32F);
            query.at<float>(0, 0) = static_cast<float>(nodes[i].second);
            query.at<float>(0, 1) = static_cast<float>(nodes[i].first);

            cv::Mat indices, dists;

            int num_found = kdtree.radiusSearch(query, indices, dists, merge_distance_px * merge_distance_px,
                                                100, cv::flann::SearchParams(32));

            if (verbose && i < 5) {
                log("  ノード " + std::to_string(i) + " で " + std::to_string(num_found) + " 個の近接ノードを発見", verbose);
            }

            // Record close pairs (excluding self)
            if (num_found > 0 && !indices.empty()) {
                for (int k = 0; k < num_found && k < indices.cols; ++k) {
                    size_t j = static_cast<size_t>(indices.at<int>(0, k));
                    if (i < j) {  // Avoid duplicates
                        close_pairs.insert({i, j});
                    }
                }
            }
        }

        if (verbose) {
            log("  見つかった近接ペア数: " + std::to_string(close_pairs.size()), verbose);
        }

        // Process close pairs
        size_t pair_count = 0;
        size_t merge_count = 0;
        size_t skip_already_removed = 0;
        size_t skip_collision = 0;

        for (const auto& pair : close_pairs) {
            pair_count++;
            if (verbose && pair_count % 100 == 0) {
                log("  処理中: " + std::to_string(pair_count) + "/" + std::to_string(close_pairs.size()) + " ペア", verbose);
            }

            size_t i = pair.first;
            size_t j = pair.second;

            if (!graph.has_node(nodes[i]) || !graph.has_node(nodes[j])) {
                skip_already_removed++;
                continue;  // Already removed
            }

            const NodeId& n1 = nodes[i];
            const NodeId& n2 = nodes[j];

            // Check if n2's neighbors can connect to n1
            auto n2_neighbors = graph.neighbors(n2);
            bool can_merge = true;

            for (const auto& neighbor : n2_neighbors) {
                if (neighbor == n1) continue;

                cv::Point p1(n1.second, n1.first);
                cv::Point p2(neighbor.second, neighbor.first);

                if (check_line_collision(p1, p2, inflated_map)) {
                    can_merge = false;
                    skip_collision++;
                    break;
                }
            }

            if (can_merge) {
                // Transfer all edges from n2 to n1
                for (const auto& neighbor : n2_neighbors) {
                    if (neighbor != n1) {
                        double edge_dist = euclidean_distance(n1, neighbor);
                        graph.add_edge(n1, neighbor, EdgeData(edge_dist, "merge"));
                    }
                }

                // Remove n2
                graph.remove_node(n2);
                merged = true;
                merge_count++;
            }
        }

        if (verbose) {
            log("  統合したペア: " + std::to_string(merge_count), verbose);
            log("  スキップ（既削除）: " + std::to_string(skip_already_removed), verbose);
            log("  スキップ（衝突）: " + std::to_string(skip_collision), verbose);
        }

        if (verbose) {
            log("  反復 " + std::to_string(iteration) + " 完了: " +
                std::to_string(initial_num_nodes - graph.num_nodes()) + "個のノードを削除", verbose);
        }

        if (!merged) {
            break;
        }
    }

    size_t num_removed = initial_num_nodes - graph.num_nodes();
    log("近接ノードを統合: " + std::to_string(num_removed) + "個のノードを削除（" +
        std::to_string(iteration) + "回の反復）", verbose);

    return num_removed;
}

size_t GraphPruner::remove_small_subgraphs(
    Graph& graph,
    double min_subgraph_length_px,
    bool verbose
) {
    size_t initial_num_nodes = graph.num_nodes();

    // Find connected components
    auto components = graph.get_connected_components();
    log(std::to_string(components.size()) + "個の連結成分を検出", verbose);

    // Remove small components
    for (const auto& component : components) {
        // Calculate total edge length
        Graph subgraph = graph.get_subgraph(component);
        double total_length = 0.0;

        for (const auto& edge : subgraph.edges()) {
            const auto& edge_data = subgraph.get_edge_data(edge.first, edge.second);
            total_length += edge_data.weight;
        }

        if (total_length < min_subgraph_length_px) {
            if (verbose) {
                log("小さな部分グラフを削除: " + std::to_string(component.size()) +
                    "個のノード, 合計長 " + std::to_string(static_cast<int>(total_length)) + "px", verbose);
            }

            // Remove all nodes in this component
            for (const auto& node : component) {
                graph.remove_node(node);
            }
        }
    }

    size_t num_removed = initial_num_nodes - graph.num_nodes();
    log("小さな部分グラフから " + std::to_string(num_removed) + "個のノードを削除", verbose);

    return num_removed;
}

void GraphPruner::prune_graph(
    Graph& graph,
    const Step1Data& step1_data,
    double merge_distance,
    double min_subgraph_length,
    bool verbose
) {
    log("============================================================", verbose);
    log("Step 6: グラフ刈り込み", verbose);
    log("============================================================", verbose);

    size_t initial_num_nodes = graph.num_nodes();
    size_t initial_num_edges = graph.num_edges();

    log("初期グラフ: " + std::to_string(initial_num_nodes) + "個のノード, " +
        std::to_string(initial_num_edges) + "個のエッジ", verbose);

    // Convert thresholds to pixels
    double merge_distance_px = merge_distance / step1_data.resolution;
    double min_subgraph_length_px = min_subgraph_length / step1_data.resolution;

    log("統合距離: " + std::to_string(merge_distance) + "m = " +
        std::to_string(static_cast<int>(merge_distance_px)) + "px", verbose);
    log("最小部分グラフ長: " + std::to_string(min_subgraph_length) + "m = " +
        std::to_string(static_cast<int>(min_subgraph_length_px)) + "px", verbose);

    // Merge close nodes
    merge_close_nodes(graph, step1_data.inflated_map, merge_distance_px, verbose);

    // Remove small subgraphs
    remove_small_subgraphs(graph, min_subgraph_length_px, verbose);

    log("最終グラフ: " + std::to_string(graph.num_nodes()) + "個のノード, " +
        std::to_string(graph.num_edges()) + "個のエッジ", verbose);
    log("Step 6 刈り込み完了！", verbose);
}

void GraphPruner::to_world_coordinates(
    Graph& graph,
    const Step1Data& step1_data
) {
    std::cout << "世界座標に変換中..." << std::endl;

    // For each node, compute and store world coordinates
    for (const auto& node : graph.nodes()) {
        NodeData& data = graph.get_node_data(node);

        // Compute world coordinates (simplified - assuming no rotation and offset)
        WorldCoord world;
        world.x = node.second * step1_data.resolution;
        world.y = node.first * step1_data.resolution;
        world.z = 0.0;

        data.world = world;
    }

    // Scale edge weights by resolution
    for (const auto& edge : graph.edges()) {
        EdgeData& data = graph.get_edge_data(edge.first, edge.second);
        data.weight *= step1_data.resolution;
    }

    std::cout << "世界座標変換完了" << std::endl;
}

} // namespace swagger
