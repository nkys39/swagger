#include "step5_delaunay.hpp"
#include <iostream>
#include <set>
#include <opencv2/opencv.hpp>

namespace swagger {

void DelaunayShortcuts::log(const std::string& message, bool verbose) {
    if (verbose) {
        std::cout << message << std::endl;
    }
}

bool DelaunayShortcuts::check_line_collision(
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

void DelaunayShortcuts::add_delaunay_shortcuts(
    Graph& graph,
    const Step1Data& step1_data,
    bool verbose
) {
    log("============================================================", verbose);
    log("Step 5: Delaunayショートカット追加", verbose);
    log("============================================================", verbose);

    auto nodes = graph.nodes();
    if (nodes.size() < 3) {
        log("警告: Delaunay三角分割には少なくとも3個のノードが必要です", verbose);
        return;
    }

    log(std::to_string(nodes.size()) + "個のノードのDelaunay三角分割を計算中...", verbose);

    // Set up bounding rectangle for Subdiv2D
    cv::Rect rect(0, 0, step1_data.original_map.cols, step1_data.original_map.rows);
    cv::Subdiv2D subdiv(rect);

    // Create mapping from point to NodeId (using vector since Point2f doesn't have operator<)
    std::vector<std::pair<cv::Point2f, NodeId>> point_to_node;

    // Insert all nodes
    for (const auto& node : nodes) {
        cv::Point2f pt(static_cast<float>(node.second), static_cast<float>(node.first));
        subdiv.insert(pt);
        point_to_node.push_back({pt, node});
    }

    // Get triangles
    std::vector<cv::Vec6f> triangle_list;
    subdiv.getTriangleList(triangle_list);

    log(std::to_string(triangle_list.size()) + "個の三角形を生成しました", verbose);

    // Collect candidate edges from triangles
    std::set<std::pair<NodeId, NodeId>> edge_candidates;

    for (const auto& t : triangle_list) {
        // Triangle vertices
        cv::Point2f pt[3];
        pt[0] = cv::Point2f(t[0], t[1]);
        pt[1] = cv::Point2f(t[2], t[3]);
        pt[2] = cv::Point2f(t[4], t[5]);

        // Check if triangle is within bounds
        bool valid = true;
        for (int i = 0; i < 3; ++i) {
            if (!rect.contains(pt[i])) {
                valid = false;
                break;
            }
        }

        if (!valid) continue;

        // Find NodeIds for each vertex
        NodeId node_ids[3];
        bool all_found = true;

        for (int i = 0; i < 3; ++i) {
            // Find nearest node with tolerance
            bool found = false;
            float best_dist_sq = 2.0f;  // Tolerance of sqrt(2)

            for (const auto& [key, value] : point_to_node) {
                float dx = key.x - pt[i].x;
                float dy = key.y - pt[i].y;
                float dist_sq = dx * dx + dy * dy;

                if (dist_sq < best_dist_sq) {
                    node_ids[i] = value;
                    best_dist_sq = dist_sq;
                    found = true;

                    // If exact match, stop searching
                    if (dist_sq < 0.01f) {
                        break;
                    }
                }
            }

            if (!found) {
                all_found = false;
                break;
            }
        }

        if (!all_found) continue;

        // Add three edges of the triangle
        for (int i = 0; i < 3; ++i) {
            NodeId n1 = node_ids[i];
            NodeId n2 = node_ids[(i + 1) % 3];

            // Normalize edge (always store smaller node first)
            auto edge = n1 < n2 ? std::make_pair(n1, n2) : std::make_pair(n2, n1);

            // Only add if edge doesn't already exist in graph
            if (!graph.has_edge(n1, n2)) {
                edge_candidates.insert(edge);
            }
        }
    }

    log(std::to_string(edge_candidates.size()) + "個の候補エッジを見つけました", verbose);

    // Add valid (collision-free) edges
    size_t initial_num_edges = graph.num_edges();
    size_t edges_added = 0;

    for (const auto& [n1, n2] : edge_candidates) {
        cv::Point p1(n1.second, n1.first);
        cv::Point p2(n2.second, n2.first);

        if (!check_line_collision(p1, p2, step1_data.inflated_map)) {
            double dist = euclidean_distance(n1, n2);
            graph.add_edge(n1, n2, EdgeData(dist, "delaunay"));
            edges_added++;
        }
    }

    log(std::to_string(edges_added) + "個のDelaunayショートカットエッジを追加しました", verbose);
    log("合計グラフ: " + std::to_string(graph.num_nodes()) + "個のノード, " +
        std::to_string(graph.num_edges()) + "個のエッジ", verbose);
    log("Step 5 完了！", verbose);
}

} // namespace swagger
