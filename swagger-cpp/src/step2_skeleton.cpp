#include "step2_skeleton.hpp"
#include <iostream>

namespace swagger {

cv::Mat SkeletonGraphBuilder::compute_skeleton(const cv::Mat& binary_map) {
    // OpenCV's thinning algorithm
    cv::Mat skeleton = binary_map.clone();
    cv::ximgproc::thinning(skeleton, skeleton, cv::ximgproc::THINNING_ZHANGSUEN);
    return skeleton;
}

void SkeletonGraphBuilder::extract_skeleton_edges(
    const cv::Mat& skeleton,
    Graph& graph,
    int sample_distance_px
) {
    // TODO: Extract skeleton paths and create nodes/edges
    // Placeholder implementation
    std::cout << "Step2: Skeleton graph generation (placeholder)" << std::endl;
}

void SkeletonGraphBuilder::build_skeleton_graph(
    Graph& graph,
    const Step1Data& step1_data,
    double skeleton_sample_distance,
    bool verbose
) {
    if (verbose) {
        std::cout << "Step 2: スケルトングラフ生成 (実装中)" << std::endl;
    }

    // Compute skeleton
    cv::Mat skeleton = compute_skeleton(1 - step1_data.inflated_map);

    int sample_distance_px = static_cast<int>(skeleton_sample_distance / step1_data.resolution);
    extract_skeleton_edges(skeleton, graph, sample_distance_px);
}

} // namespace swagger
