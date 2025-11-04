#include "graph.hpp"
#include "map_processor.hpp"
#include "boundary_sampler.hpp"
#include "file_writer.hpp"
#include <iostream>
#include <string>
#include <cstring>

void print_usage(const char* program_name) {
    std::cout << "使用方法: " << program_name << " [オプション]\n\n";
    std::cout << "必須引数:\n";
    std::cout << "  --map <パス>              占有グリッドマップのパス（PNG/PGM形式）\n\n";
    std::cout << "オプション引数:\n";
    std::cout << "  --output <パス>           出力ディレクトリ（デフォルト: output）\n";
    std::cout << "  --resolution <値>         マップ解像度（m/px、デフォルト: 0.05）\n";
    std::cout << "  --safety-distance <値>    ロボット半径（m、デフォルト: 0.5）\n";
    std::cout << "  --occupancy-threshold <値> 占有閾値（0-255、デフォルト: 127）\n";
    std::cout << "  --boundary-inflation-factor <値>  境界膨張係数（デフォルト: 1.5）\n";
    std::cout << "  --boundary-sample-distance <値>   サンプリング距離（m、デフォルト: 2.5）\n";
    std::cout << "  --save-gml                GML形式で保存\n";
    std::cout << "  --save-graphml            GraphML形式で保存\n";
    std::cout << "  --quiet                   ログ出力を抑制\n";
    std::cout << "  --help                    このヘルプを表示\n";
}

struct Config {
    std::string map_path;
    std::string output_dir = "output";
    double resolution = 0.05;
    double safety_distance = 0.5;
    int occupancy_threshold = 127;
    double boundary_inflation_factor = 1.5;
    double boundary_sample_distance = 2.5;
    bool save_gml = false;
    bool save_graphml = false;
    bool verbose = true;
};

bool parse_args(int argc, char* argv[], Config& config) {
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];

        if (arg == "--help" || arg == "-h") {
            print_usage(argv[0]);
            return false;
        }
        else if (arg == "--map") {
            if (i + 1 < argc) {
                config.map_path = argv[++i];
            } else {
                std::cerr << "エラー: --map requires an argument" << std::endl;
                return false;
            }
        }
        else if (arg == "--output") {
            if (i + 1 < argc) {
                config.output_dir = argv[++i];
            } else {
                std::cerr << "エラー: --output requires an argument" << std::endl;
                return false;
            }
        }
        else if (arg == "--resolution") {
            if (i + 1 < argc) {
                config.resolution = std::stod(argv[++i]);
            } else {
                std::cerr << "エラー: --resolution requires an argument" << std::endl;
                return false;
            }
        }
        else if (arg == "--safety-distance") {
            if (i + 1 < argc) {
                config.safety_distance = std::stod(argv[++i]);
            } else {
                std::cerr << "エラー: --safety-distance requires an argument" << std::endl;
                return false;
            }
        }
        else if (arg == "--occupancy-threshold") {
            if (i + 1 < argc) {
                config.occupancy_threshold = std::stoi(argv[++i]);
            } else {
                std::cerr << "エラー: --occupancy-threshold requires an argument" << std::endl;
                return false;
            }
        }
        else if (arg == "--boundary-inflation-factor") {
            if (i + 1 < argc) {
                config.boundary_inflation_factor = std::stod(argv[++i]);
            } else {
                std::cerr << "エラー: --boundary-inflation-factor requires an argument" << std::endl;
                return false;
            }
        }
        else if (arg == "--boundary-sample-distance") {
            if (i + 1 < argc) {
                config.boundary_sample_distance = std::stod(argv[++i]);
            } else {
                std::cerr << "エラー: --boundary-sample-distance requires an argument" << std::endl;
                return false;
            }
        }
        else if (arg == "--save-gml") {
            config.save_gml = true;
        }
        else if (arg == "--save-graphml") {
            config.save_graphml = true;
        }
        else if (arg == "--quiet" || arg == "-q") {
            config.verbose = false;
        }
        else {
            std::cerr << "エラー: 不明な引数: " << arg << std::endl;
            return false;
        }
    }

    // Check required arguments
    if (config.map_path.empty()) {
        std::cerr << "エラー: --map is required" << std::endl;
        print_usage(argv[0]);
        return false;
    }

    return true;
}

int main(int argc, char* argv[]) {
    Config config;

    // Parse command line arguments
    if (!parse_args(argc, argv, config)) {
        return 1;
    }

    try {
        if (config.verbose) {
            std::cout << "============================================================" << std::endl;
            std::cout << "SWAGGER Minimal: Step1 + Step3 (C++版)" << std::endl;
            std::cout << "============================================================" << std::endl;
        }

        // Step 1: Preprocess
        swagger::Step1Data step1_data = swagger::MapProcessor::preprocess(
            config.map_path,
            config.resolution,
            config.safety_distance,
            config.occupancy_threshold,
            config.verbose
        );

        // Step 3: Boundary sampling
        swagger::Graph graph;
        swagger::BoundarySampler::sample_boundaries(
            graph,
            step1_data,
            config.boundary_inflation_factor,
            config.boundary_sample_distance,
            config.verbose
        );

        // Save results
        swagger::FileWriter::save_all(
            graph,
            step1_data,
            config.output_dir,
            config.save_gml,
            config.save_graphml,
            config.verbose
        );

        if (config.verbose) {
            std::cout << "============================================================" << std::endl;
            std::cout << "全処理完了！" << std::endl;
            std::cout << "結果は " << config.output_dir << " ディレクトリに保存されました" << std::endl;
            std::cout << "============================================================" << std::endl;
        }

        return 0;

    } catch (const std::exception& e) {
        std::cerr << "エラー: " << e.what() << std::endl;
        return 1;
    }
}
