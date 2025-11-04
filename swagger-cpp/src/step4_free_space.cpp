#include "step4_free_space.hpp"
#include <iostream>
#include <queue>
#include <limits>
#include <cmath>
#include <opencv2/flann.hpp>

namespace swagger {

void FreeSpaceSampler::log(const std::string& message, bool verbose) {
    if (verbose) {
        std::cout << message << std::endl;
    }
}

bool FreeSpaceSampler::check_line_collision(
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

void FreeSpaceSampler::sample_free_space(
    Graph& graph,
    const Step1Data& step1_data,
    double distance_threshold,
    bool verbose
) {
    log("============================================================", verbose);
    log("Step 4: フリースペースサンプリング", verbose);
    log("============================================================", verbose);

    size_t initial_num_nodes = graph.num_nodes();

    // Convert threshold to pixels
    int distance_threshold_px = static_cast<int>(distance_threshold / step1_data.resolution);
    log("距離閾値: " + std::to_string(distance_threshold) + "m = " +
        std::to_string(distance_threshold_px) + "px", verbose);

    // Initialize distance map
    cv::Mat distance_map(step1_data.original_map.size(), CV_32F, cv::Scalar(std::numeric_limits<float>::max()));

    // Set occupied pixels to 0
    for (int y = 0; y < step1_data.free_map.rows; ++y) {
        for (int x = 0; x < step1_data.free_map.cols; ++x) {
            if (step1_data.free_map.at<uchar>(y, x) == 0) {
                distance_map.at<float>(y, x) = 0.0f;
            }
        }
    }

    // Set existing node pixels to 0
    auto existing_nodes = graph.nodes();
    for (const auto& node : existing_nodes) {
        distance_map.at<float>(node.first, node.second) = 0.0f;
    }

    // Iterative sampling
    int iteration = 0;
    int max_iterations = 20;

    while (iteration < max_iterations) {
        iteration++;

        // Create binary mask for distance transform
        cv::Mat binary_mask(distance_map.size(), CV_8U);
        for (int y = 0; y < distance_map.rows; ++y) {
            for (int x = 0; x < distance_map.cols; ++x) {
                binary_mask.at<uchar>(y, x) = (distance_map.at<float>(y, x) > 0) ? 255 : 0;
            }
        }

        // Compute distance transform
        cv::Mat dist_transform;
        cv::distanceTransform(binary_mask, dist_transform, cv::DIST_L2, cv::DIST_MASK_PRECISE);

        // Find areas with large distances
        cv::Mat large_distance_areas;
        cv::threshold(dist_transform, large_distance_areas, distance_threshold_px, 255, cv::THRESH_BINARY);
        large_distance_areas.convertTo(large_distance_areas, CV_8U);

        if (cv::countNonZero(large_distance_areas) == 0) {
            log("フリースペースサンプリングが収束しました（反復回数: " + std::to_string(iteration) + "）", verbose);
            break;
        }

        // Find local maxima using dilation
        cv::Mat kernel = cv::getStructuringElement(cv::MORPH_RECT, cv::Size(3, 3));
        cv::Mat dilated;
        cv::dilate(dist_transform, dilated, kernel);

        // Find local maxima
        cv::Mat local_maxima_mask;
        cv::compare(dist_transform, dilated, local_maxima_mask, cv::CMP_EQ);
        cv::bitwise_and(local_maxima_mask, large_distance_areas, local_maxima_mask);

        // Extract local maxima coordinates
        std::vector<cv::Point> local_maxima;
        for (int y = 0; y < local_maxima_mask.rows; ++y) {
            for (int x = 0; x < local_maxima_mask.cols; ++x) {
                if (local_maxima_mask.at<uchar>(y, x) > 0) {
                    local_maxima.push_back(cv::Point(x, y));
                }
            }
        }

        // Add local maxima as nodes using KD-tree for efficient proximity search
        int nodes_added_this_iter = 0;
        double half_threshold = distance_threshold_px / 2.0;

        // Build KD-tree from existing nodes
        auto existing_nodes = graph.nodes();
        if (!existing_nodes.empty()) {
            cv::Mat node_coords(existing_nodes.size(), 2, CV_32F);
            for (size_t i = 0; i < existing_nodes.size(); ++i) {
                node_coords.at<float>(i, 0) = static_cast<float>(existing_nodes[i].second);  // x (col)
                node_coords.at<float>(i, 1) = static_cast<float>(existing_nodes[i].first);   // y (row)
            }

            cv::flann::Index kdtree(node_coords, cv::flann::KDTreeIndexParams(1), cvflann::FLANN_DIST_EUCLIDEAN);

            for (const auto& point : local_maxima) {
                NodeId candidate(point.y, point.x);

                // Query KD-tree for nearest neighbor within half threshold
                cv::Mat query(1, 2, CV_32F);
                query.at<float>(0, 0) = static_cast<float>(point.x);
                query.at<float>(0, 1) = static_cast<float>(point.y);

                std::vector<int> indices(1);
                std::vector<float> dists(1);

                kdtree.knnSearch(query, indices, dists, 1, cv::flann::SearchParams(32));

                // Check if nearest neighbor is within half threshold
                bool too_close = (dists[0] < half_threshold * half_threshold);  // squared distance

                if (!too_close) {
                    graph.add_node(candidate, NodeData("free_space"));
                    distance_map.at<float>(point.y, point.x) = 0.0f;
                    nodes_added_this_iter++;
                }
            }
        } else {
            // No existing nodes, add all local maxima
            for (const auto& point : local_maxima) {
                NodeId candidate(point.y, point.x);
                graph.add_node(candidate, NodeData("free_space"));
                distance_map.at<float>(point.y, point.x) = 0.0f;
                nodes_added_this_iter++;
            }
        }

        if (nodes_added_this_iter == 0) {
            log("反復 " + std::to_string(iteration) + ": 新しいノードが追加されませんでした", verbose);
            break;
        }

        if (verbose) {
            log("反復 " + std::to_string(iteration) + ": " + std::to_string(nodes_added_this_iter) + "個のノードを追加", verbose);
        }
    }

    // Connect new nodes to nearby existing nodes
    auto all_nodes = graph.nodes();
    std::vector<NodeId> new_nodes(all_nodes.begin() + initial_num_nodes, all_nodes.end());

    log("新しいノードを近傍ノードと接続中...", verbose);

    for (const auto& new_node : new_nodes) {
        const auto& new_node_data = graph.get_node_data(new_node);
        if (new_node_data.node_type != "free_space") {
            continue;
        }

        // Find closest nodes within connection range
        double connection_range = 3.0 * distance_threshold_px;
        std::vector<std::pair<double, NodeId>> candidates;

        for (const auto& node : all_nodes) {
            if (node == new_node) continue;

            double dist = euclidean_distance(new_node, node);
            if (dist <= connection_range) {
                candidates.push_back({dist, node});
            }
        }

        // Sort by distance and connect to closest nodes
        std::sort(candidates.begin(), candidates.end());

        int max_connections = 5;
        int connections_made = 0;

        for (const auto& [dist, node] : candidates) {
            if (connections_made >= max_connections) break;

            // Check collision
            cv::Point p1(new_node.second, new_node.first);
            cv::Point p2(node.second, node.first);

            if (!check_line_collision(p1, p2, step1_data.inflated_map)) {
                graph.add_edge(new_node, node, EdgeData(dist, "free_space"));
                connections_made++;
            }
        }
    }

    size_t num_nodes_added = graph.num_nodes() - initial_num_nodes;
    log(std::to_string(num_nodes_added) + "個のフリースペースノードを追加しました", verbose);
    log("合計グラフ: " + std::to_string(graph.num_nodes()) + "個のノード, " +
        std::to_string(graph.num_edges()) + "個のエッジ", verbose);
    log("Step 4 完了！", verbose);
}

} // namespace swagger
