#include <opencv2/opencv.hpp>
#include <iostream>

int main() {
    // Create blank map (500x500, all white = free space)
    cv::Mat map_img(500, 500, CV_8UC1, cv::Scalar(255));

    // Add rectangular obstacles (black = occupied)
    cv::rectangle(map_img, cv::Point(100, 100), cv::Point(400, 150), cv::Scalar(0), -1);
    cv::rectangle(map_img, cv::Point(100, 200), cv::Point(150, 400), cv::Scalar(0), -1);
    cv::rectangle(map_img, cv::Point(300, 250), cv::Point(400, 400), cv::Scalar(0), -1);

    // Add circular obstacle
    cv::circle(map_img, cv::Point(250, 350), 50, cv::Scalar(0), -1);

    // Save
    std::string output_path = "sample_map.png";
    cv::imwrite(output_path, map_img);

    std::cout << "サンプルマップを作成しました: " << output_path << std::endl;
    std::cout << "マップサイズ: " << map_img.rows << "x" << map_img.cols << std::endl;
    std::cout << "自由空間（白）: 255" << std::endl;
    std::cout << "占有空間（黒）: 0" << std::endl;

    return 0;
}
