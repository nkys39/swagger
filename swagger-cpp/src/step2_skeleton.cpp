#include "step2_skeleton.hpp"
#include <iostream>
#include <iomanip>
#include <queue>
#include <set>
#include <cmath>
#include <algorithm>
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

int SkeletonGraphBuilder::count_neighbors(const cv::Mat& skeleton, int y, int x) {
    // Count 8-connected neighbors
    int count = 0;
    for (int dy = -1; dy <= 1; ++dy) {
        for (int dx = -1; dx <= 1; ++dx) {
            if (dy == 0 && dx == 0) continue;

            int ny = y + dy;
            int nx = x + dx;

            if (ny >= 0 && ny < skeleton.rows && nx >= 0 && nx < skeleton.cols) {
                if (skeleton.at<uchar>(ny, nx) > 0) {
                    count++;
                }
            }
        }
    }
    return count;
}

std::vector<cv::Point> SkeletonGraphBuilder::find_junction_points(const cv::Mat& skeleton) {
    // Junction points have 3 or more neighbors
    std::vector<cv::Point> junctions;

    for (int y = 0; y < skeleton.rows; ++y) {
        for (int x = 0; x < skeleton.cols; ++x) {
            if (skeleton.at<uchar>(y, x) > 0) {
                int neighbors = count_neighbors(skeleton, y, x);
                if (neighbors >= 3) {
                    junctions.push_back(cv::Point(x, y));
                }
            }
        }
    }

    return junctions;
}

std::vector<cv::Point> SkeletonGraphBuilder::find_endpoint_points(const cv::Mat& skeleton) {
    // Endpoint points have exactly 1 neighbor
    std::vector<cv::Point> endpoints;

    for (int y = 0; y < skeleton.rows; ++y) {
        for (int x = 0; x < skeleton.cols; ++x) {
            if (skeleton.at<uchar>(y, x) > 0) {
                int neighbors = count_neighbors(skeleton, y, x);
                if (neighbors == 1) {
                    endpoints.push_back(cv::Point(x, y));
                }
            }
        }
    }

    return endpoints;
}

void SkeletonGraphBuilder::trace_branch(
    const cv::Mat& skeleton,
    cv::Mat& visited,
    cv::Point start,
    cv::Point previous,
    std::vector<cv::Point>& branch_coords,
    const std::vector<cv::Point>& junctions,
    const std::vector<cv::Point>& endpoints
) {
    // Trace along the skeleton from start point until we hit a junction or endpoint
    cv::Point current = start;
    branch_coords.push_back(current);
    visited.at<uchar>(current.y, current.x) = 255;

    while (true) {
        // Find next unvisited neighbor
        cv::Point next(-1, -1);
        int neighbor_count = 0;

        for (int dy = -1; dy <= 1; ++dy) {
            for (int dx = -1; dx <= 1; ++dx) {
                if (dy == 0 && dx == 0) continue;

                int ny = current.y + dy;
                int nx = current.x + dx;

                if (ny < 0 || ny >= skeleton.rows || nx < 0 || nx >= skeleton.cols) continue;

                if (skeleton.at<uchar>(ny, nx) > 0 && visited.at<uchar>(ny, nx) == 0) {
                    if (cv::Point(nx, ny) != previous) {
                        neighbor_count++;
                        next = cv::Point(nx, ny);
                    }
                }
            }
        }

        // If no unvisited neighbors, we've reached the end
        if (neighbor_count == 0) {
            break;
        }

        // Move to next point
        previous = current;
        current = next;
        branch_coords.push_back(current);
        visited.at<uchar>(current.y, current.x) = 255;

        // Check if we've reached a junction or endpoint
        bool is_junction = std::find(junctions.begin(), junctions.end(), current) != junctions.end();
        bool is_endpoint = std::find(endpoints.begin(), endpoints.end(), current) != endpoints.end();

        if (is_junction || is_endpoint) {
            break;
        }
    }
}

std::vector<SkeletonBranch> SkeletonGraphBuilder::extract_branches(
    const cv::Mat& skeleton,
    const std::vector<cv::Point>& junctions,
    const std::vector<cv::Point>& endpoints
) {
    std::vector<SkeletonBranch> branches;
    cv::Mat visited = cv::Mat::zeros(skeleton.size(), CV_8U);

    // Mark junctions and endpoints as not visited initially
    // Start tracing from each junction's neighbors
    for (const auto& junction : junctions) {
        // Find all neighbors of this junction
        for (int dy = -1; dy <= 1; ++dy) {
            for (int dx = -1; dx <= 1; ++dx) {
                if (dy == 0 && dx == 0) continue;

                int ny = junction.y + dy;
                int nx = junction.x + dx;

                if (ny < 0 || ny >= skeleton.rows || nx < 0 || nx >= skeleton.cols) continue;

                cv::Point neighbor(nx, ny);
                if (skeleton.at<uchar>(ny, nx) > 0 && visited.at<uchar>(ny, nx) == 0) {
                    // Trace this branch
                    SkeletonBranch branch;
                    branch.coordinates.push_back(junction);  // Start from junction
                    branch.start_junction_id = -1;  // Will be set later if needed
                    branch.end_junction_id = -1;

                    std::vector<cv::Point> branch_coords;
                    trace_branch(skeleton, visited, neighbor, junction, branch_coords, junctions, endpoints);

                    // Add the traced coordinates
                    branch.coordinates.insert(branch.coordinates.end(), branch_coords.begin(), branch_coords.end());

                    if (branch.coordinates.size() > 1) {
                        branches.push_back(branch);
                    }
                }
            }
        }
    }

    // Also trace from endpoints
    for (const auto& endpoint : endpoints) {
        if (visited.at<uchar>(endpoint.y, endpoint.x) == 0) {
            SkeletonBranch branch;
            branch.start_junction_id = -1;
            branch.end_junction_id = -1;

            std::vector<cv::Point> branch_coords;
            trace_branch(skeleton, visited, endpoint, cv::Point(-1, -1), branch_coords, junctions, endpoints);

            branch.coordinates = branch_coords;

            if (branch.coordinates.size() > 1) {
                branches.push_back(branch);
            }
        }
    }

    return branches;
}

void SkeletonGraphBuilder::add_branch_to_graph(
    Graph& graph,
    const SkeletonBranch& branch,
    int sample_distance_px,
    const cv::Mat& inflated_map
) {
    if (branch.coordinates.empty()) return;

    // Sample points along the branch
    int num_segments = std::max(1, static_cast<int>(branch.coordinates.size()) / sample_distance_px);
    int segment_length = branch.coordinates.size() / num_segments;

    for (int i = 0; i < num_segments; ++i) {
        int start_idx = i * segment_length;
        int end_idx = std::min((i + 1) * segment_length, static_cast<int>(branch.coordinates.size()) - 1);

        cv::Point start = branch.coordinates[start_idx];
        cv::Point end = branch.coordinates[end_idx];

        // Check collision
        if (check_line_collision(start, end, inflated_map)) {
            continue;
        }

        // Add edge
        NodeId n1(start.y, start.x);
        NodeId n2(end.y, end.x);

        graph.add_node(n1, NodeData("skeleton"));
        graph.add_node(n2, NodeData("skeleton"));

        double dist = euclidean_distance(n1, n2);
        graph.add_edge(n1, n2, EdgeData(dist, "skeleton"));
    }
}

void SkeletonGraphBuilder::build_skeleton_graph(
    Graph& graph,
    const Step1Data& step1_data,
    double skeleton_sample_distance,
    bool verbose
) {
    log("============================================================", verbose);
    log("Step 2: スケルトングラフ生成（トポロジー解析付き）", verbose);
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

    // Find junction and endpoint points (topology analysis)
    log("トポロジー解析を実行中...", verbose);
    std::vector<cv::Point> junctions = find_junction_points(skeleton);
    std::vector<cv::Point> endpoints = find_endpoint_points(skeleton);

    log("分岐点: " + std::to_string(junctions.size()) + "個", verbose);
    log("終端点: " + std::to_string(endpoints.size()) + "個", verbose);

    // Extract branches from skeleton
    log("ブランチを抽出中...", verbose);
    std::vector<SkeletonBranch> branches = extract_branches(skeleton, junctions, endpoints);
    log("抽出されたブランチ数: " + std::to_string(branches.size()), verbose);

    // Calculate branch statistics
    if (verbose && !branches.empty()) {
        double total_length = 0;
        int min_length = INT_MAX;
        int max_length = 0;
        for (const auto& branch : branches) {
            int len = branch.coordinates.size();
            total_length += len;
            min_length = std::min(min_length, len);
            max_length = std::max(max_length, len);
        }
        double avg_length = total_length / branches.size();
        log("ブランチ統計:", verbose);
        log("  平均長: " + std::to_string(static_cast<int>(avg_length)) + "px", verbose);
        log("  最小長: " + std::to_string(min_length) + "px", verbose);
        log("  最大長: " + std::to_string(max_length) + "px", verbose);
    }

    // Sample points along branches
    int sample_distance_px = static_cast<int>(skeleton_sample_distance / step1_data.resolution);
    log("サンプリング距離: " + std::to_string(skeleton_sample_distance) + "m = " +
        std::to_string(sample_distance_px) + "px", verbose);

    size_t initial_num_nodes = graph.num_nodes();
    size_t initial_num_edges = graph.num_edges();

    // Add each branch to the graph
    for (const auto& branch : branches) {
        add_branch_to_graph(graph, branch, sample_distance_px, step1_data.inflated_map);
    }

    size_t num_nodes_added = graph.num_nodes() - initial_num_nodes;
    size_t num_edges_added = graph.num_edges() - initial_num_edges;

    log(std::to_string(num_nodes_added) + "個のスケルトンノードを追加しました", verbose);
    log(std::to_string(num_edges_added) + "個のスケルトンエッジを追加しました", verbose);
    log("合計グラフ: " + std::to_string(graph.num_nodes()) + "個のノード, " +
        std::to_string(graph.num_edges()) + "個のエッジ", verbose);
    log("Step 2 完了！", verbose);
}

} // namespace swagger
