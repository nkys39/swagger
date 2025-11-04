#pragma once

#include "graph.hpp"
#include "utils.hpp"
#include <opencv2/opencv.hpp>

namespace swagger {

class FreeSpaceSampler {
public:
    // Sample nodes in free space areas
    static void sample_free_space(
        Graph& graph,
        const Step1Data& step1_data,
        double distance_threshold,
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
