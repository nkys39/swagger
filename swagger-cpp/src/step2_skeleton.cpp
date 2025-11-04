#include "step2_skeleton.hpp"
#include <iostream>
#include <iomanip>
#include <queue>
#include <set>
#include <cmath>
#include <opencv2/ximgproc.hpp>

namespace swagger {

void SkeletonGraphBuilder::log(const std::string& message, bool verbose) {
    if (verbose) {
        std::cout << message << std::endl;
    }
}

bool SkeletonGraphBuilder::check_line_collision(
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

cv::Mat SkeletonGraphBuilder::compute_skeleton(const cv::Mat& free_map) {
    // Ensure we have a binary image
    cv::Mat binary = free_map.clone();
    if (binary.type() != CV_8UC1) {
        binary.convertTo(binary, CV_8UC1);
    }

    // Threshold to ensure binary (0 or 255)
    cv::threshold(binary, binary, 127, 255, cv::THRESH_BINARY);

    // Apply thinning to get skeleton
    cv::Mat skeleton;
    cv::ximgproc::thinning(binary, skeleton, cv::ximgproc::THINNING_ZHANGSUEN);

    return skeleton;
}

std::vector<NodeId> SkeletonGraphBuilder::sample_skeleton_points(
    const cv::Mat& skeleton,
    int sample_distance_px
) {
    std::vector<NodeId> sampled_points;
    std::set<NodeId> visited;

    // Find all skeleton pixels
    std::vector<cv::Point> skeleton_pixels;
    for (int y = 0; y < skeleton.rows; ++y) {
        for (int x = 0; x < skeleton.cols; ++x) {
            if (skeleton.at<uchar>(y, x) > 0) {
                skeleton_pixels.push_back(cv::Point(x, y));
            }
        }
    }

    if (skeleton_pixels.empty()) {
        return sampled_points;
    }

    // Sample points at regular intervals
    for (const auto& pixel : skeleton_pixels) {
        NodeId node(pixel.y, pixel.x);

        // Check if this point is far enough from already sampled points
        bool too_close = false;
        for (const auto& sampled : sampled_points) {
            double dist = euclidean_distance(node, sampled);
            if (dist < sample_distance_px) {
                too_close = true;
                break;
            }
        }

        if (!too_close) {
            sampled_points.push_back(node);
        }
    }

    return sampled_points;
}

void SkeletonGraphBuilder::connect_skeleton_nodes(
    const std::vector<NodeId>& nodes,
    Graph& graph,
    const cv::Mat& inflated_map,
    double max_connection_distance
) {
    // For each pair of nodes, try to connect if they're close enough
    for (size_t i = 0; i < nodes.size(); ++i) {
        const NodeId& n1 = nodes[i];

        for (size_t j = i + 1; j < nodes.size(); ++j) {
            const NodeId& n2 = nodes[j];

            // Check distance
            double dist = euclidean_distance(n1, n2);
            if (dist > max_connection_distance) {
                continue;
            }

            // Check collision
            cv::Point p1(n1.second, n1.first);
            cv::Point p2(n2.second, n2.first);

            if (!check_line_collision(p1, p2, inflated_map)) {
                graph.add_edge(n1, n2, EdgeData(dist, "skeleton"));
            }
        }
    }
}

void SkeletonGraphBuilder::build_skeleton_graph(
    Graph& graph,
    const Step1Data& step1_data,
    double skeleton_sample_distance,
    bool verbose
) {
    log("============================================================", verbose);
    log("Step 2: スケルトングラフ生成", verbose);
    log("============================================================", verbose);

    // Check if we have a valid map
    if (step1_data.inflated_map.empty()) {
        log("警告: 膨張マップがありません - スケルトン生成をスキップします", verbose);
        return;
    }

    // Create free space map (inverse of inflated map)
    cv::Mat free_map = ~step1_data.inflated_map;

    // Check if map is completely free
    if (cv::countNonZero(free_map) == 0) {
        log("警告: 自由空間がありません - スケルトン生成をスキップします", verbose);
        return;
    }

    // Compute skeleton
    log("スケルトン（medial axis）を計算中...", verbose);
    cv::Mat skeleton = compute_skeleton(free_map);

    int skeleton_pixels = cv::countNonZero(skeleton);
    log("スケルトン画素数: " + std::to_string(skeleton_pixels), verbose);

    if (skeleton_pixels == 0) {
        log("警告: スケルトンが生成されませんでした", verbose);
        return;
    }

    // Sample points along skeleton
    int sample_distance_px = static_cast<int>(skeleton_sample_distance / step1_data.resolution);
    log("サンプリング距離: " + std::to_string(skeleton_sample_distance) + "m = " +
        std::to_string(sample_distance_px) + "px", verbose);

    std::vector<NodeId> sampled_nodes = sample_skeleton_points(skeleton, sample_distance_px);
    log("サンプリングしたノード数: " + std::to_string(sampled_nodes.size()), verbose);

    // Add nodes to graph
    size_t initial_num_nodes = graph.num_nodes();
    for (const auto& node : sampled_nodes) {
        graph.add_node(node, NodeData("skeleton"));
    }

    // Connect nearby nodes (within 3x sample distance)
    double max_connection_distance = 3.0 * sample_distance_px;
    log("ノードを接続中（最大距離: " + std::to_string(static_cast<int>(max_connection_distance)) + "px）...", verbose);

    connect_skeleton_nodes(sampled_nodes, graph, step1_data.inflated_map, max_connection_distance);

    size_t num_nodes_added = graph.num_nodes() - initial_num_nodes;
    log(std::to_string(num_nodes_added) + "個のスケルトンノードを追加しました", verbose);
    log("合計グラフ: " + std::to_string(graph.num_nodes()) + "個のノード, " +
        std::to_string(graph.num_edges()) + "個のエッジ", verbose);
    log("Step 2 完了！", verbose);
}

} // namespace swagger
