#include "map_processor.hpp"
#include <iostream>
#include <stdexcept>

namespace swagger {

void MapProcessor::log(const std::string& message, bool verbose) {
    if (verbose) {
        std::cout << message << std::endl;
    }
}

cv::Mat MapProcessor::load_map(const std::string& map_path) {
    cv::Mat map = cv::imread(map_path, cv::IMREAD_GRAYSCALE);
    if (map.empty()) {
        throw std::runtime_error("Failed to load map from: " + map_path);
    }
    return map;
}

void MapProcessor::distance_transform(
    const cv::Mat& free_map,
    double resolution,
    double safety_distance,
    cv::Mat& dist_transform_out,
    cv::Mat& inflated_map_out
) {
    // Pad the binary map by 1 pixel
    cv::Mat padded;
    cv::copyMakeBorder(free_map, padded, 1, 1, 1, 1, cv::BORDER_CONSTANT, cv::Scalar(0));

    // Compute distance transform
    cv::Mat dist_full;
    cv::distanceTransform(padded, dist_full, cv::DIST_L2, cv::DIST_MASK_PRECISE);

    // Filter by safety distance
    double threshold_px = safety_distance / resolution;
    cv::Mat inflated_full;
    cv::compare(dist_full, threshold_px, inflated_full, cv::CMP_LT);
    inflated_full.convertTo(inflated_full, CV_8U);

    // Remove padding
    dist_transform_out = dist_full(cv::Rect(1, 1, free_map.cols, free_map.rows)).clone();
    inflated_map_out = inflated_full(cv::Rect(1, 1, free_map.cols, free_map.rows)).clone();
}

Step1Data MapProcessor::preprocess(
    const std::string& map_path,
    double resolution,
    double safety_distance,
    int occupancy_threshold,
    bool verbose
) {
    log("============================================================", verbose);
    log("Step 1: 前処理", verbose);
    log("============================================================", verbose);

    Step1Data data;
    data.resolution = resolution;
    data.safety_distance = safety_distance;
    data.occupancy_threshold = occupancy_threshold;

    // Load map
    log("マップを読み込み中: " + map_path, verbose);
    data.original_map = load_map(map_path);
    log("マップサイズ: " + std::to_string(data.original_map.rows) + "x" +
        std::to_string(data.original_map.cols), verbose);

    // Log parameters
    if (verbose) {
        std::cout << "パラメータ:" << std::endl;
        std::cout << "  解像度: " << resolution << " m/px" << std::endl;
        std::cout << "  安全距離: " << safety_distance << " m" << std::endl;
        std::cout << "  占有閾値: " << occupancy_threshold << std::endl;
    }

    // Create free space map
    cv::Mat free_map_bool = data.original_map > occupancy_threshold;
    free_map_bool.convertTo(data.free_map, CV_8U, 255.0);
    cv::threshold(data.free_map, data.free_map, 127, 255, cv::THRESH_BINARY);
    int free_pixels = cv::countNonZero(data.free_map);
    int total_pixels = data.free_map.rows * data.free_map.cols;
    double free_percentage = (static_cast<double>(free_pixels) / total_pixels) * 100.0;

    if (verbose) {
        std::cout << "自由空間: " << free_pixels << "/" << total_pixels
                  << " ピクセル (" << std::fixed << std::setprecision(1)
                  << free_percentage << "%)" << std::endl;
    }

    // Check if map is completely free
    if (free_pixels == total_pixels) {
        log("警告: マップは完全に自由空間です - 障害物が検出されませんでした！", verbose);
        log("距離変換をスキップ", verbose);
        data.dist_transform = cv::Mat();
        data.inflated_map = cv::Mat::zeros(data.free_map.size(), CV_8U);
    } else {
        // Compute distance transform
        log("距離変換を計算中...", verbose);
        distance_transform(
            data.free_map,
            resolution,
            safety_distance,
            data.dist_transform,
            data.inflated_map
        );
        log("距離変換完了", verbose);
    }

    log("Step 1 完了！", verbose);
    return data;
}

} // namespace swagger
