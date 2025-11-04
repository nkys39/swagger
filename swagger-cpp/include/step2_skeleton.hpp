#pragma once

#include "graph.hpp"
#include "utils.hpp"
#include <opencv2/opencv.hpp>

namespace swagger {

// Structure to represent a branch/path in the skeleton
struct SkeletonBranch {
    std::vector<cv::Point> coordinates;
    int start_junction_id;  // -1 if starts at endpoint
    int end_junction_id;    // -1 if ends at endpoint
};

class SkeletonGraphBuilder {
public:
    // Build graph from skeleton of inflated map
    static void build_skeleton_graph(
        Graph& graph,
        const Step1Data& step1_data,
        double skeleton_sample_distance,
        bool verbose = true
    );

private:
    static void log(const std::string& message, bool verbose);

    static bool check_line_collision(
        const cv::Point& p0,
        const cv::Point& p1,
        const cv::Mat& inflated_map
    );

    static cv::Mat compute_skeleton(const cv::Mat& free_map);

    // Topology analysis methods (similar to skan library)
    static std::vector<cv::Point> find_junction_points(const cv::Mat& skeleton);
    static std::vector<cv::Point> find_endpoint_points(const cv::Mat& skeleton);
    static int count_neighbors(const cv::Mat& skeleton, int y, int x);

    static std::vector<SkeletonBranch> extract_branches(
        const cv::Mat& skeleton,
        const std::vector<cv::Point>& junctions,
        const std::vector<cv::Point>& endpoints
    );

    static void trace_branch(
        const cv::Mat& skeleton,
        cv::Mat& visited,
        cv::Point start,
        cv::Point previous,
        std::vector<cv::Point>& branch_coords,
        const std::vector<cv::Point>& junctions,
        const std::vector<cv::Point>& endpoints
    );

    static void add_branch_to_graph(
        Graph& graph,
        const SkeletonBranch& branch,
        int sample_distance_px,
        const cv::Mat& inflated_map
    );
};

} // namespace swagger
