#pragma once

#include "graph.hpp"
#include "utils.hpp"
#include <opencv2/opencv.hpp>

namespace swagger {

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

    static std::vector<NodeId> sample_skeleton_points(
        const cv::Mat& skeleton,
        int sample_distance_px
    );

    static void connect_skeleton_nodes(
        const std::vector<NodeId>& nodes,
        Graph& graph,
        const cv::Mat& inflated_map,
        double max_connection_distance
    );
};

} // namespace swagger
