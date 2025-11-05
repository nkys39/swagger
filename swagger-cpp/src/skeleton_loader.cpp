#include "skeleton_loader.hpp"
#include <fstream>
#include <sstream>
#include <iostream>
#include <vector>
#include <cmath>

namespace swagger {

void SkeletonLoader::log(const std::string& message, bool verbose) {
    if (verbose) {
        std::cout << message << std::endl;
    }
}

// Find matching closing bracket
size_t find_matching_bracket(const std::string& str, size_t start_pos) {
    int depth = 0;
    for (size_t i = start_pos; i < str.length(); ++i) {
        if (str[i] == '[') depth++;
        else if (str[i] == ']') {
            depth--;
            if (depth == 0) return i;
        }
    }
    return std::string::npos;
}

// Extract numbers from a string like "[83, 400]"
bool parse_pair(const std::string& str, int& first, int& second) {
    size_t start = str.find('[');
    size_t comma = str.find(',', start);
    size_t end = str.find(']', comma);

    if (start == std::string::npos || comma == std::string::npos || end == std::string::npos) {
        return false;
    }

    try {
        first = std::stoi(str.substr(start + 1, comma - start - 1));
        second = std::stoi(str.substr(comma + 1, end - comma - 1));
        return true;
    } catch (...) {
        return false;
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

    // Find "nodes" array
    size_t nodes_start = json_content.find("\"nodes\"");
    if (nodes_start == std::string::npos) {
        log("エラー: JSON内にnodesが見つかりませんでした", verbose);
        return false;
    }

    // Find the opening bracket of nodes array
    size_t nodes_bracket_start = json_content.find('[', nodes_start);
    if (nodes_bracket_start == std::string::npos) {
        log("エラー: nodes配列の開始が見つかりませんでした", verbose);
        return false;
    }

    // Find the matching closing bracket
    size_t nodes_bracket_end = find_matching_bracket(json_content, nodes_bracket_start);
    if (nodes_bracket_end == std::string::npos) {
        log("エラー: nodes配列の終了が見つかりませんでした", verbose);
        return false;
    }

    // Extract nodes array content
    std::string nodes_str = json_content.substr(
        nodes_bracket_start,
        nodes_bracket_end - nodes_bracket_start + 1
    );

    // Parse individual nodes
    int node_count = 0;
    size_t pos = 0;
    while ((pos = nodes_str.find('[', pos + 1)) != std::string::npos) {
        size_t end = nodes_str.find(']', pos);
        if (end == std::string::npos) break;

        std::string node_str = nodes_str.substr(pos, end - pos + 1);
        int row, col;
        if (parse_pair(node_str, row, col)) {
            NodeId node_id(row, col);
            graph.add_node(node_id, NodeData("skeleton"));
            node_count++;
        }

        pos = end;
    }

    // Find "edges" array
    size_t edges_start = json_content.find("\"edges\"", nodes_bracket_end);
    int edge_count = 0;

    if (edges_start != std::string::npos) {
        size_t edges_bracket_start = json_content.find('[', edges_start);
        if (edges_bracket_start != std::string::npos) {
            size_t edges_bracket_end = find_matching_bracket(json_content, edges_bracket_start);

            if (edges_bracket_end != std::string::npos) {
                std::string edges_str = json_content.substr(
                    edges_bracket_start,
                    edges_bracket_end - edges_bracket_start + 1
                );

                // Parse individual edges
                pos = 0;
                while ((pos = edges_str.find("\"start\"", pos)) != std::string::npos) {
                    // Find start coordinates
                    size_t start_bracket = edges_str.find('[', pos);
                    if (start_bracket == std::string::npos) break;

                    size_t start_bracket_end = edges_str.find(']', start_bracket);
                    if (start_bracket_end == std::string::npos) break;

                    std::string start_str = edges_str.substr(
                        start_bracket,
                        start_bracket_end - start_bracket + 1
                    );

                    int start_row, start_col;
                    if (!parse_pair(start_str, start_row, start_col)) {
                        pos = start_bracket_end;
                        continue;
                    }

                    // Find end coordinates
                    size_t end_pos = edges_str.find("\"end\"", start_bracket_end);
                    if (end_pos == std::string::npos) break;

                    size_t end_bracket = edges_str.find('[', end_pos);
                    if (end_bracket == std::string::npos) break;

                    size_t end_bracket_end = edges_str.find(']', end_bracket);
                    if (end_bracket_end == std::string::npos) break;

                    std::string end_str = edges_str.substr(
                        end_bracket,
                        end_bracket_end - end_bracket + 1
                    );

                    int end_row, end_col;
                    if (!parse_pair(end_str, end_row, end_col)) {
                        pos = end_bracket_end;
                        continue;
                    }

                    // Add edge to graph
                    NodeId start_id(start_row, start_col);
                    NodeId end_id(end_row, end_col);

                    double dy = end_row - start_row;
                    double dx = end_col - start_col;
                    double distance = std::sqrt(dx * dx + dy * dy);

                    graph.add_edge(start_id, end_id, EdgeData(distance, "skeleton"));
                    edge_count++;

                    pos = end_bracket_end;
                }
            }
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
