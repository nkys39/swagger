#pragma once

#include <opencv2/opencv.hpp>
#include <string>

namespace swagger {

struct Step1Data {
    cv::Mat original_map;
    cv::Mat free_map;
    cv::Mat dist_transform;
    cv::Mat inflated_map;
    double resolution;
    double safety_distance;
    int occupancy_threshold;

    Step1Data() : resolution(0.05), safety_distance(0.5), occupancy_threshold(127) {}
};

class MapProcessor {
public:
    MapProcessor() = default;

    // Load occupancy grid map
    static cv::Mat load_map(const std::string& map_path);

    // Step 1: Preprocess map and compute distance transform
    static Step1Data preprocess(
        const std::string& map_path,
        double resolution,
        double safety_distance,
        int occupancy_threshold,
        bool verbose = true
    );

private:
    // Compute distance transform and inflate obstacles
    static void distance_transform(
        const cv::Mat& free_map,
        double resolution,
        double safety_distance,
        cv::Mat& dist_transform_out,
        cv::Mat& inflated_map_out
    );

    static void log(const std::string& message, bool verbose);
};

} // namespace swagger
