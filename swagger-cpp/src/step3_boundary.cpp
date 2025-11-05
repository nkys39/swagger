#include "step3_boundary.hpp"
#include <iostream>
#include <iomanip>
#include <cmath>

namespace swagger {

void BoundarySampler::log(const std::string& message, bool verbose) {
    if (verbose) {
        std::cout << message << std::endl;
    }
}

bool BoundarySampler::check_line_collision(
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
            return true;  // Out of bounds = collision
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

std::vector<std::vector<cv::Point>> BoundarySampler::find_obstacle_contours(
    const cv::Mat& dist_transform,
    double boundary_inflation_px
) {
    // Filter obstacles by boundary inflation
    cv::Mat filtered;
    cv::threshold(dist_transform, filtered, boundary_inflation_px, 255, cv::THRESH_BINARY);
    filtered.convertTo(filtered, CV_8U);

    // Find contours
    std::vector<std::vector<cv::Point>> contours;
    std::vector<cv::Vec4i> hierarchy;
    cv::findContours(filtered, contours, hierarchy, cv::RETR_LIST, cv::CHAIN_APPROX_TC89_KCOS);

    return contours;
}

void BoundarySampler::connect_contour_nodes(
    const std::vector<NodeId>& contour_nodes,
    Graph& graph,
    const cv::Mat& inflated_map
) {
    size_t n = contour_nodes.size();
    for (size_t i = 0; i < n; ++i) {
        const NodeId& n1 = contour_nodes[i];
        const NodeId& n2 = contour_nodes[(i + 1) % n];

        // Convert to cv::Point for collision check
        cv::Point p1(n1.second, n1.first);
        cv::Point p2(n2.second, n2.first);

        if (!check_line_collision(p1, p2, inflated_map)) {
            double dist = euclidean_distance(n1, n2);
            graph.add_edge(n1, n2, EdgeData(dist, "contour"));
        }
    }
}

void BoundarySampler::sample_boundaries(
    Graph& graph,
    const Step1Data& step1_data,
    double boundary_inflation_factor,
    double boundary_sample_distance,
    bool verbose
) {
    log("============================================================", verbose);
    log("Step 3: 障害物境界サンプリング", verbose);
    log("============================================================", verbose);

    // Check if distance transform is available
    if (step1_data.dist_transform.empty()) {
        log("警告: 距離変換がありません - 境界サンプリングをスキップします", verbose);
        return;
    }

    // Convert parameters to pixels
    double boundary_inflation_px = boundary_inflation_factor * step1_data.safety_distance / step1_data.resolution;
    int sample_distance_px = static_cast<int>(boundary_sample_distance / step1_data.resolution);

    if (verbose) {
        std::cout << "境界膨張: " << boundary_inflation_factor << " * "
                  << step1_data.safety_distance << "m = "
                  << std::fixed << std::setprecision(1) << boundary_inflation_px << "px" << std::endl;
        std::cout << "サンプル距離: " << boundary_sample_distance << "m = "
                  << sample_distance_px << "px" << std::endl;
    }

    // Find contours
    log("障害物輪郭を検出中（膨張: " + std::to_string(static_cast<int>(boundary_inflation_px)) + "px）...", verbose);
    auto contours = find_obstacle_contours(step1_data.dist_transform, boundary_inflation_px);
    log(std::to_string(contours.size()) + "個の輪郭を検出しました", verbose);

    if (verbose) {
        // Show contour details for debugging
        size_t total_contour_vertices = 0;
        for (const auto& contour : contours) {
            total_contour_vertices += contour.size();
        }
        log("  輪郭の総頂点数: " + std::to_string(total_contour_vertices), verbose);
    }

    size_t initial_num_nodes = graph.num_nodes();

    // Process each contour
    for (const auto& contour : contours) {
        std::vector<NodeId> contour_nodes;

        // Process each vertex in the contour
        for (size_t i = 0; i < contour.size(); ++i) {
            const cv::Point& p1 = contour[i];
            const cv::Point& p2 = contour[(i + 1) % contour.size()];

            // Add first vertex
            NodeId node1(p1.y, p1.x);
            contour_nodes.push_back(node1);
            graph.add_node(node1, NodeData("boundary"));

            // Calculate distance to next vertex
            double segment_length = cv::norm(p2 - p1);

            // Add intermediate points
            // Match Python's implementation: np.linspace(p1, p2, num=num_intermediate, endpoint=False)[1:]
            int num_intermediate = static_cast<int>(segment_length / sample_distance_px);
            if (num_intermediate > 0) {
                // Generate points using linspace logic (endpoint=False)
                for (int j = 1; j < num_intermediate; ++j) {
                    // Python: np.linspace divides the range into num_intermediate equal parts
                    // and takes points at fractions j/num_intermediate (j = 0, 1, ..., num_intermediate-1)
                    // Then [1:] skips the first point (j=0)
                    double t = static_cast<double>(j) / static_cast<double>(num_intermediate);

                    // Calculate floating point coordinates first, then convert to int
                    // This matches Python's: linspace(...).astype(int)
                    double fx = p1.x + t * (p2.x - p1.x);
                    double fy = p1.y + t * (p2.y - p1.y);

                    int x = static_cast<int>(fx);
                    int y = static_cast<int>(fy);

                    NodeId node(y, x);
                    contour_nodes.push_back(node);
                    graph.add_node(node, NodeData("boundary"));
                }
            }
        }

        // Connect nodes along this contour
        connect_contour_nodes(contour_nodes, graph, step1_data.inflated_map);
    }

    size_t num_nodes_added = graph.num_nodes() - initial_num_nodes;
    log(std::to_string(num_nodes_added) + "個の境界ノードを追加しました", verbose);
    log("合計グラフ: " + std::to_string(graph.num_nodes()) + "個のノード, " +
        std::to_string(graph.num_edges()) + "個のエッジ", verbose);
    log("Step 3 完了！", verbose);
}

} // namespace swagger
