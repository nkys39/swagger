#pragma once

#include "graph.hpp"
#include "utils.hpp"
#include <opencv2/opencv.hpp>

namespace swagger {

class GraphPruner {
public:
    // Prune graph: merge close nodes and remove small subgraphs
    static void prune_graph(
        Graph& graph,
        const Step1Data& step1_data,
        double merge_distance,
        double min_subgraph_length,
        bool verbose = true
    );

    // Convert to world coordinates
    static void to_world_coordinates(
        Graph& graph,
        const Step1Data& step1_data
    );

private:
    static void log(const std::string& message, bool verbose);

    static bool check_line_collision(
        const cv::Point& p0,
        const cv::Point& p1,
        const cv::Mat& inflated_map
    );

    static size_t merge_close_nodes(
        Graph& graph,
        const cv::Mat& inflated_map,
        double merge_distance_px,
        bool verbose
    );

    static size_t remove_small_subgraphs(
        Graph& graph,
        double min_subgraph_length_px,
        bool verbose
    );
};

} // namespace swagger
