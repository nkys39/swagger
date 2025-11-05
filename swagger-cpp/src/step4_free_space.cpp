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
    // Python uses while True (infinite loop), we set a very high limit to match
    int iteration = 0;
    int max_iterations = 10000;  // Very high limit to match Python's while True behavior

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

        // CRITICAL FIX: Track nodes added in THIS iteration
        // This matches Python's behavior where idx.insert() immediately adds to R-tree
        std::vector<cv::Point> nodes_added_in_this_iteration;

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
                bool too_close = false;

                // Check 1: Query KD-tree for existing nodes (from before this iteration)
                cv::Mat query(1, 2, CV_32F);
                query.at<float>(0, 0) = static_cast<float>(point.x);
                query.at<float>(0, 1) = static_cast<float>(point.y);

                cv::Mat indices, dists;
                int num_found = kdtree.radiusSearch(query, indices, dists,
                                                    half_threshold * half_threshold,
                                                    100, cv::flann::SearchParams(32));

                if (num_found > 0) {
                    too_close = true;
                }

                // Check 2: CRITICAL - Check nodes added in THIS iteration
                // This matches Python's: idx.insert(len(graph.nodes) - 1, (col, row, col, row))
                if (!too_close) {
                    for (const auto& added : nodes_added_in_this_iteration) {
                        double dx = point.x - added.x;
                        double dy = point.y - added.y;
                        double dist_sq = dx * dx + dy * dy;

                        if (dist_sq < half_threshold * half_threshold) {
                            too_close = true;
                            break;
                        }
                    }
                }

                // Only add node if NO nodes (existing or newly-added) are within half_threshold
                if (!too_close) {
                    graph.add_node(candidate, NodeData("free_space"));
                    distance_map.at<float>(point.y, point.x) = 0.0f;
                    nodes_added_in_this_iteration.push_back(point);  // Track for subsequent checks
                    nodes_added_this_iter++;
                }
            }
        } else {
            // No existing nodes, but still need to check nodes added in this iteration
            for (const auto& point : local_maxima) {
                NodeId candidate(point.y, point.x);
                bool too_close = false;

                // Check nodes added in this iteration
                for (const auto& added : nodes_added_in_this_iteration) {
                    double dx = point.x - added.x;
                    double dy = point.y - added.y;
                    double dist_sq = dx * dx + dy * dy;

                    if (dist_sq < half_threshold * half_threshold) {
                        too_close = true;
                        break;
                    }
                }

                if (!too_close) {
                    graph.add_node(candidate, NodeData("free_space"));
                    distance_map.at<float>(point.y, point.x) = 0.0f;
                    nodes_added_in_this_iteration.push_back(point);
                    nodes_added_this_iter++;
                }
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

    // Python implementation does NOT add edges in Step 4, only nodes
    // Edges are added in later steps (Step 5 Delaunay shortcuts, etc.)

    size_t num_nodes_added = graph.num_nodes() - initial_num_nodes;
    log(std::to_string(num_nodes_added) + "個のフリースペースノードを追加しました", verbose);
    log("合計グラフ: " + std::to_string(graph.num_nodes()) + "個のノード, " +
        std::to_string(graph.num_edges()) + "個のエッジ", verbose);
    log("Step 4 完了！", verbose);
}

} // namespace swagger
