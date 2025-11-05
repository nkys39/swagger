#include "graph.hpp"
#include "step1_preprocess.hpp"
#include "step2_skeleton.hpp"
#include "step3_boundary.hpp"
#include "step4_free_space.hpp"
#include "step5_delaunay.hpp"
#include "step6_prune.hpp"
#include "skeleton_loader.hpp"
#include "file_writer.hpp"
#include "utils.hpp"
#include <iostream>
#include <string>
#include <cstring>

void print_usage(const char* program_name) {
    std::cout << "使用方法: " << program_name << " [オプション]\n\n";
    std::cout << "必須引数:\n";
    std::cout << "  --map <パス>              占有グリッドマップのパス（PNG/PGM形式）\n\n";
    std::cout << "基本オプション:\n";
    std::cout << "  --output <パス>           出力ディレクトリ（デフォルト: output）\n";
    std::cout << "  --resolution <値>         マップ解像度（m/px、デフォルト: 0.05）\n";
    std::cout << "  --safety-distance <値>    ロボット半径（m、デフォルト: 0.5）\n";
    std::cout << "  --occupancy-threshold <値> 占有閾値（0-255、デフォルト: 127）\n";
    std::cout << "  --save-gml                GML形式で保存\n";
    std::cout << "  --save-graphml            GraphML形式で保存\n";
    std::cout << "  --quiet                   ログ出力を抑制\n";
    std::cout << "  --help                    このヘルプを表示\n\n";
    std::cout << "ステップ制御（デフォルト: 全て有効）:\n";
    std::cout << "  --use-skeleton            Step2: スケルトングラフを生成\n";
    std::cout << "  --use-boundary            Step3: 境界サンプリングを有効化\n";
    std::cout << "  --use-free-space          Step4: フリースペースサンプリングを有効化\n";
    std::cout << "  --use-delaunay            Step5: Delaunayショートカットを追加\n";
    std::cout << "  --prune                   Step6: グラフを刈り込む\n\n";
    std::cout << "Step 2 パラメータ:\n";
    std::cout << "  --skeleton-from-json <パス>      PythonでエクスポートしたJSONからスケルトンを読み込む\n";
    std::cout << "  --skeleton-sample-distance <値>  サンプリング距離（m、デフォルト: 1.5）\n\n";
    std::cout << "Step 3 パラメータ:\n";
    std::cout << "  --boundary-inflation-factor <値>  境界膨張係数（デフォルト: 1.5）\n";
    std::cout << "  --boundary-sample-distance <値>   サンプリング距離（m、デフォルト: 2.5）\n\n";
    std::cout << "Step 4 パラメータ:\n";
    std::cout << "  --free-space-threshold <値>  距離閾値（m、デフォルト: 1.5）\n\n";
    std::cout << "Step 6 パラメータ:\n";
    std::cout << "  --merge-distance <値>     ノード統合距離（m、デフォルト: 0.25）\n";
    std::cout << "  --min-subgraph-length <値> 最小部分グラフ長（m、デフォルト: 0.25）\n";
}

struct Config {
    std::string map_path;
    std::string output_dir = "output";
    double resolution = 0.05;
    double safety_distance = 0.5;
    int occupancy_threshold = 127;

    // Step 2: Skeleton
    bool use_skeleton = true;  // Default: enabled
    std::string skeleton_json_path;  // If set, load skeleton from JSON instead
    double skeleton_sample_distance = 1.5;

    // Step 3: Boundary
    bool use_boundary = true;  // Default: enabled
    double boundary_inflation_factor = 1.5;
    double boundary_sample_distance = 2.5;

    // Step 4: Free space
    bool use_free_space = true;  // Default: enabled
    double free_space_threshold = 1.5;

    // Step 5: Delaunay
    bool use_delaunay = true;  // Default: enabled

    // Step 6: Pruning
    bool prune = true;  // Default: enabled
    double merge_distance = 0.25;
    double min_subgraph_length = 0.25;

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
        // Step 2: Skeleton
        else if (arg == "--use-skeleton") {
            config.use_skeleton = true;
        }
        else if (arg == "--skeleton-from-json") {
            if (i + 1 < argc) {
                config.skeleton_json_path = argv[++i];
                config.use_skeleton = true;  // Enable skeleton when using JSON
            } else {
                std::cerr << "エラー: --skeleton-from-json requires an argument" << std::endl;
                return false;
            }
        }
        else if (arg == "--skeleton-sample-distance") {
            if (i + 1 < argc) {
                config.skeleton_sample_distance = std::stod(argv[++i]);
            } else {
                std::cerr << "エラー: --skeleton-sample-distance requires an argument" << std::endl;
                return false;
            }
        }
        // Step 3: Boundary
        else if (arg == "--use-boundary") {
            config.use_boundary = true;
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
        // Step 4: Free space
        else if (arg == "--use-free-space") {
            config.use_free_space = true;
        }
        else if (arg == "--free-space-threshold") {
            if (i + 1 < argc) {
                config.free_space_threshold = std::stod(argv[++i]);
            } else {
                std::cerr << "エラー: --free-space-threshold requires an argument" << std::endl;
                return false;
            }
        }
        // Step 5: Delaunay
        else if (arg == "--use-delaunay") {
            config.use_delaunay = true;
        }
        // Step 6: Pruning
        else if (arg == "--prune") {
            config.prune = true;
        }
        else if (arg == "--merge-distance") {
            if (i + 1 < argc) {
                config.merge_distance = std::stod(argv[++i]);
            } else {
                std::cerr << "エラー: --merge-distance requires an argument" << std::endl;
                return false;
            }
        }
        else if (arg == "--min-subgraph-length") {
            if (i + 1 < argc) {
                config.min_subgraph_length = std::stod(argv[++i]);
            } else {
                std::cerr << "エラー: --min-subgraph-length requires an argument" << std::endl;
                return false;
            }
        }
        // Output options
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
            std::cout << "SWAGGER C++: 完全実装版（Step 1-6）" << std::endl;
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

        swagger::Graph graph;

        // Step 2: Skeleton graph (optional)
        if (config.use_skeleton) {
            if (!config.skeleton_json_path.empty()) {
                // Load skeleton from JSON (exported from Python)
                if (!swagger::SkeletonLoader::load_from_json(
                    graph,
                    config.skeleton_json_path,
                    config.verbose
                )) {
                    std::cerr << "エラー: スケルトンJSONの読み込みに失敗しました" << std::endl;
                    return 1;
                }
            } else {
                // Generate skeleton using C++ implementation
                swagger::SkeletonGraphBuilder::build_skeleton_graph(
                    graph,
                    step1_data,
                    config.skeleton_sample_distance,
                    config.verbose
                );
            }
            if (config.verbose) {
                graph.print_statistics("Step 2後");
                // Save visualization
                swagger::FileWriter::save_visualization(graph, step1_data, config.output_dir + "/cpp_step2.png");
            }
        }

        // Step 3: Boundary sampling (default: enabled)
        if (config.use_boundary) {
            swagger::BoundarySampler::sample_boundaries(
                graph,
                step1_data,
                config.boundary_inflation_factor,
                config.boundary_sample_distance,
                config.verbose
            );
            if (config.verbose) {
                graph.print_statistics("Step 3後");
                // Save visualization
                swagger::FileWriter::save_visualization(graph, step1_data, config.output_dir + "/cpp_step3.png");
            }
        }

        // Step 4: Free space sampling (optional)
        if (config.use_free_space) {
            swagger::FreeSpaceSampler::sample_free_space(
                graph,
                step1_data,
                config.free_space_threshold,
                config.verbose
            );
            if (config.verbose) {
                graph.print_statistics("Step 4後");
                // Save visualization
                swagger::FileWriter::save_visualization(graph, step1_data, config.output_dir + "/cpp_step4.png");
            }
        }

        // Step 5: Delaunay shortcuts (optional)
        if (config.use_delaunay) {
            swagger::DelaunayShortcuts::add_delaunay_shortcuts(
                graph,
                step1_data,
                config.verbose
            );
            if (config.verbose) {
                graph.print_statistics("Step 5後");
                // Save visualization
                swagger::FileWriter::save_visualization(graph, step1_data, config.output_dir + "/cpp_step5.png");
            }
        }

        // Step 6: Graph pruning (optional)
        if (config.prune) {
            swagger::GraphPruner::prune_graph(
                graph,
                step1_data,
                config.merge_distance,
                config.min_subgraph_length,
                config.verbose
            );

            // Convert to world coordinates
            swagger::GraphPruner::to_world_coordinates(graph, step1_data);

            if (config.verbose) {
                graph.print_statistics("Step 6後（最終）");
                // Save visualization
                swagger::FileWriter::save_visualization(graph, step1_data, config.output_dir + "/cpp_step6.png");
            }
        }

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
