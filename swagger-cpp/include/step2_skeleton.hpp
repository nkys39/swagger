#pragma once

#include "graph.hpp"
#include "utils.hpp"

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
    static cv::Mat compute_skeleton(const cv::Mat& binary_map);
    static void extract_skeleton_edges(
        const cv::Mat& skeleton,
        Graph& graph,
        int sample_distance_px
    );
};

} // namespace swagger
