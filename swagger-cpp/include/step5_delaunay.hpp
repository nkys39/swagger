#pragma once

#include "graph.hpp"
#include "utils.hpp"
#include <opencv2/opencv.hpp>

namespace swagger {

class DelaunayShortcuts {
public:
    // Add shortcuts based on Delaunay triangulation
    static void add_delaunay_shortcuts(
        Graph& graph,
        const Step1Data& step1_data,
        bool verbose = true
    );

private:
    static void log(const std::string& message, bool verbose);

    static bool check_line_collision(
        const cv::Point& p0,
        const cv::Point& p1,
        const cv::Mat& inflated_map
    );
};

} // namespace swagger
