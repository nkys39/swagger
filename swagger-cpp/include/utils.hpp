#pragma once

#include <opencv2/opencv.hpp>
#include "graph.hpp"

namespace swagger {

// Configuration structure
struct WaypointGraphConfig {
    // Step 2: Skeleton
    double skeleton_sample_distance = 1.5;  // meters
    bool use_skeleton_graph = true;

    // Step 3: Boundary
    double boundary_inflation_factor = 1.5;
    double boundary_sample_distance = 2.5;  // meters
    bool use_boundary_sampling = true;

    // Step 4: Free space
    double free_space_sampling_threshold = 1.5;  // meters
    bool use_free_space_sampling = true;

    // Step 5: Delaunay
    bool use_delaunay_shortcuts = true;

    // Step 6: Prune
    double merge_node_distance = 0.25;  // meters
    double min_subgraph_length = 0.25;  // meters
    bool prune_graph = true;
};

// Step 1 data structure
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

// Coordinate conversion functions
inline cv::Point node_to_point(const NodeId& node) {
    return cv::Point(node.second, node.first);
}

inline NodeId point_to_node(const cv::Point& point) {
    return NodeId(point.y, point.x);
}

// World coordinate conversion
struct WorldCoord {
    double x, y, z;
    WorldCoord() : x(0), y(0), z(0) {}
    WorldCoord(double x_, double y_, double z_ = 0.0) : x(x_), y(y_), z(z_) {}
};

WorldCoord pixel_to_world(
    const NodeId& pixel,
    double resolution,
    double x_offset = 0.0,
    double y_offset = 0.0
);

NodeId world_to_pixel(
    const WorldCoord& world,
    double resolution,
    double x_offset = 0.0,
    double y_offset = 0.0
);

} // namespace swagger
