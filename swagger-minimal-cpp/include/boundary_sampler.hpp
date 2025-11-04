#pragma once

#include "graph.hpp"
#include "map_processor.hpp"
#include <opencv2/opencv.hpp>
#include <vector>

namespace swagger {

class BoundarySampler {
public:
    BoundarySampler() = default;

    // Step 3: Sample obstacle boundaries
    static void sample_boundaries(
        Graph& graph,
        const Step1Data& step1_data,
        double boundary_inflation_factor,
        double boundary_sample_distance,
        bool verbose = true
    );

private:
    // Check if line between two points intersects obstacles (Bresenham's algorithm)
    static bool check_line_collision(
        const cv::Point& p0,
        const cv::Point& p1,
        const cv::Mat& inflated_map
    );

    // Find contours of inflated obstacles
    static std::vector<std::vector<cv::Point>> find_obstacle_contours(
        const cv::Mat& dist_transform,
        double boundary_inflation_px
    );

    // Connect nodes along a contour
    static void connect_contour_nodes(
        const std::vector<NodeId>& contour_nodes,
        Graph& graph,
        const cv::Mat& inflated_map
    );

    static void log(const std::string& message, bool verbose);
};

} // namespace swagger
