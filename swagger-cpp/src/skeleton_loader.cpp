#include "skeleton_loader.hpp"
#include <fstream>
#include <sstream>
#include <iostream>
#include <vector>
#include <regex>

namespace swagger {

void SkeletonLoader::log(const std::string& message, bool verbose) {
    if (verbose) {
        std::cout << message << std::endl;
    }
}

bool SkeletonLoader::load_from_json(
    Graph& graph,
    const std::string& json_path,
    bool verbose
) {
    log("============================================================", verbose);
    log("Step 2: スケルトングラフ読み込み（JSONから）", verbose);
    log("============================================================", verbose);

    // Open JSON file
    std::ifstream file(json_path);
    if (!file.is_open()) {
        log("エラー: JSONファイルを開けませんでした: " + json_path, verbose);
        return false;
    }

    // Read entire file
    std::stringstream buffer;
    buffer << file.rdbuf();
    std::string json_content = buffer.str();
    file.close();

    log("JSONファイルを読み込みました: " + json_path, verbose);

    // Simple JSON parsing (nodes array)
    // Format: "nodes": [[row, col], [row, col], ...]
    std::regex nodes_pattern(R"("nodes"\s*:\s*\[([\s\S]*?)\])");
    std::smatch nodes_match;

    if (!std::regex_search(json_content, nodes_match, nodes_pattern)) {
        log("エラー: JSON内にnodesが見つかりませんでした", verbose);
        return false;
    }

    std::string nodes_str = nodes_match[1].str();

    // Parse individual nodes: [row, col]
    std::regex node_pattern(R"(\[\s*(\d+)\s*,\s*(\d+)\s*\])");
    auto nodes_begin = std::sregex_iterator(nodes_str.begin(), nodes_str.end(), node_pattern);
    auto nodes_end = std::sregex_iterator();

    int node_count = 0;
    for (std::sregex_iterator i = nodes_begin; i != nodes_end; ++i) {
        std::smatch match = *i;
        int row = std::stoi(match[1].str());
        int col = std::stoi(match[2].str());

        NodeId node_id(row, col);
        graph.add_node(node_id, NodeData("skeleton"));
        node_count++;
    }

    // Parse edges
    std::regex edges_pattern(R"("edges"\s*:\s*\[([\s\S]*?)\])");
    std::smatch edges_match;

    int edge_count = 0;
    if (std::regex_search(json_content, edges_match, edges_pattern)) {
        std::string edges_str = edges_match[1].str();

        // Parse individual edges
        // Format: {"start": [row, col], "end": [row, col], "type": "skeleton"}
        std::regex edge_pattern(
            R"(\{\s*"start"\s*:\s*\[\s*(\d+)\s*,\s*(\d+)\s*\]\s*,\s*)"
            R"("end"\s*:\s*\[\s*(\d+)\s*,\s*(\d+)\s*\])"
        );

        auto edges_begin = std::sregex_iterator(edges_str.begin(), edges_str.end(), edge_pattern);
        auto edges_end = std::sregex_iterator();

        for (std::sregex_iterator i = edges_begin; i != edges_end; ++i) {
            std::smatch match = *i;
            int start_row = std::stoi(match[1].str());
            int start_col = std::stoi(match[2].str());
            int end_row = std::stoi(match[3].str());
            int end_col = std::stoi(match[4].str());

            NodeId start_id(start_row, start_col);
            NodeId end_id(end_row, end_col);

            // Calculate distance
            double dy = end_row - start_row;
            double dx = end_col - start_col;
            double distance = std::sqrt(dx * dx + dy * dy);

            graph.add_edge(start_id, end_id, EdgeData(distance, "skeleton"));
            edge_count++;
        }
    }

    log(std::to_string(node_count) + "個のスケルトンノードを読み込みました", verbose);
    log(std::to_string(edge_count) + "個のスケルトンエッジを読み込みました", verbose);
    log("合計グラフ: " + std::to_string(graph.num_nodes()) + "個のノード, " +
        std::to_string(graph.num_edges()) + "個のエッジ", verbose);
    log("Step 2 完了！", verbose);

    return true;
}

} // namespace swagger
