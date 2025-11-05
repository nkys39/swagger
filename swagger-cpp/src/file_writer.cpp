#include "file_writer.hpp"
#include <fstream>
#include <iostream>
#include <iomanip>
#include <sys/stat.h>
#include <sys/types.h>

namespace swagger {

void FileWriter::log(const std::string& message, bool verbose) {
    if (verbose) {
        std::cout << message << std::endl;
    }
}

void FileWriter::create_directory(const std::string& dir_path) {
    mkdir(dir_path.c_str(), 0755);
}

void FileWriter::save_gml(const Graph& graph, const std::string& filepath) {
    std::ofstream file(filepath);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file: " + filepath);
    }

    file << "graph [\n";

    // Write nodes
    auto nodes = graph.nodes();
    for (size_t i = 0; i < nodes.size(); ++i) {
        const auto& node = nodes[i];
        const auto& data = graph.get_node_data(node);

        file << "  node [\n";
        file << "    id " << i << "\n";
        file << "    label \"(" << node.first << "," << node.second << ")\"\n";
        file << "    node_type \"" << data.node_type << "\"\n";
        file << "  ]\n";
    }

    // Create node ID lookup
    std::map<NodeId, size_t> node_to_id;
    for (size_t i = 0; i < nodes.size(); ++i) {
        node_to_id[nodes[i]] = i;
    }

    // Write edges
    auto edges = graph.edges();
    for (const auto& edge : edges) {
        const auto& data = graph.get_edge_data(edge.first, edge.second);
        size_t src_id = node_to_id[edge.first];
        size_t dst_id = node_to_id[edge.second];

        file << "  edge [\n";
        file << "    source " << src_id << "\n";
        file << "    target " << dst_id << "\n";
        file << std::fixed << std::setprecision(2);
        file << "    weight " << data.weight << "\n";
        file << "    edge_type \"" << data.edge_type << "\"\n";
        file << "  ]\n";
    }

    file << "]\n";
    file.close();
}

void FileWriter::save_graphml(const Graph& graph, const std::string& filepath) {
    std::ofstream file(filepath);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file: " + filepath);
    }

    // XML header
    file << "<?xml version='1.0' encoding='utf-8'?>\n";
    file << "<graphml xmlns=\"http://graphml.graphdrawing.org/xmlns\" "
         << "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" "
         << "xsi:schemaLocation=\"http://graphml.graphdrawing.org/xmlns "
         << "http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd\">\n";

    // Define keys
    file << "  <key id=\"d0\" for=\"node\" attr.name=\"node_type\" attr.type=\"string\" />\n";
    file << "  <key id=\"d1\" for=\"edge\" attr.name=\"weight\" attr.type=\"double\" />\n";
    file << "  <key id=\"d2\" for=\"edge\" attr.name=\"edge_type\" attr.type=\"string\" />\n";

    // Graph
    file << "  <graph edgedefault=\"undirected\">\n";

    // Write nodes
    auto nodes = graph.nodes();
    for (const auto& node : nodes) {
        const auto& data = graph.get_node_data(node);
        std::string node_id = "(" + std::to_string(node.first) + ", " + std::to_string(node.second) + ")";

        file << "    <node id=\"" << node_id << "\">\n";
        file << "      <data key=\"d0\">" << data.node_type << "</data>\n";
        file << "    </node>\n";
    }

    // Write edges
    auto edges = graph.edges();
    for (const auto& edge : edges) {
        const auto& data = graph.get_edge_data(edge.first, edge.second);
        std::string src_id = "(" + std::to_string(edge.first.first) + ", " + std::to_string(edge.first.second) + ")";
        std::string dst_id = "(" + std::to_string(edge.second.first) + ", " + std::to_string(edge.second.second) + ")";

        file << "    <edge source=\"" << src_id << "\" target=\"" << dst_id << "\">\n";
        file << std::fixed << std::setprecision(2);
        file << "      <data key=\"d1\">" << data.weight << "</data>\n";
        file << "      <data key=\"d2\">" << data.edge_type << "</data>\n";
        file << "    </edge>\n";
    }

    file << "  </graph>\n";
    file << "</graphml>\n";
    file.close();
}

void FileWriter::save_nodes_txt(const Graph& graph, const std::string& filepath) {
    std::ofstream file(filepath);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file: " + filepath);
    }

    file << "# row, col (pixel coordinates)\n";

    auto nodes = graph.nodes();
    // Sort nodes
    std::sort(nodes.begin(), nodes.end());

    for (const auto& node : nodes) {
        file << node.first << ", " << node.second << "\n";
    }

    file.close();
}

void FileWriter::save_edges_txt(const Graph& graph, const std::string& filepath) {
    std::ofstream file(filepath);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file: " + filepath);
    }

    file << "# src_row, src_col, dst_row, dst_col, weight, edge_type\n";

    auto edges = graph.edges();
    for (const auto& edge : edges) {
        const auto& data = graph.get_edge_data(edge.first, edge.second);
        file << edge.first.first << ", " << edge.first.second << ", "
             << edge.second.first << ", " << edge.second.second << ", "
             << std::fixed << std::setprecision(3) << data.weight << ", "
             << data.edge_type << "\n";
    }

    file.close();
}

void FileWriter::save_json(const Graph& graph, const std::string& filepath) {
    std::ofstream file(filepath);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open file: " + filepath);
    }

    file << "{\n";
    file << "  \"nodes\": [\n";

    auto nodes = graph.nodes();
    for (size_t i = 0; i < nodes.size(); ++i) {
        const auto& node = nodes[i];
        const auto& data = graph.get_node_data(node);

        file << "    {\n";
        file << "      \"pixel\": {\n";
        file << "        \"row\": " << node.first << ",\n";
        file << "        \"col\": " << node.second << "\n";
        file << "      },\n";
        file << "      \"node_type\": \"" << data.node_type << "\"";

        // Add world coordinates if available
        if (data.world.has_value()) {
            file << ",\n";
            file << "      \"world\": {\n";
            file << std::fixed << std::setprecision(6);
            file << "        \"x\": " << data.world.value().x << ",\n";
            file << "        \"y\": " << data.world.value().y << ",\n";
            file << "        \"z\": " << data.world.value().z << "\n";
            file << "      }\n";
        } else {
            file << "\n";
        }

        file << "    }";
        if (i < nodes.size() - 1) {
            file << ",";
        }
        file << "\n";
    }

    file << "  ],\n";
    file << "  \"edges\": [\n";

    auto edges = graph.edges();
    for (size_t i = 0; i < edges.size(); ++i) {
        const auto& edge = edges[i];
        const auto& data = graph.get_edge_data(edge.first, edge.second);

        file << "    {\n";
        file << "      \"source\": {\n";
        file << "        \"row\": " << edge.first.first << ",\n";
        file << "        \"col\": " << edge.first.second << "\n";
        file << "      },\n";
        file << "      \"target\": {\n";
        file << "        \"row\": " << edge.second.first << ",\n";
        file << "        \"col\": " << edge.second.second << "\n";
        file << "      },\n";
        file << std::fixed << std::setprecision(3);
        file << "      \"weight\": " << data.weight << ",\n";
        file << "      \"edge_type\": \"" << data.edge_type << "\"\n";
        file << "    }";
        if (i < edges.size() - 1) {
            file << ",";
        }
        file << "\n";
    }

    file << "  ]\n";
    file << "}\n";

    file.close();
}

void FileWriter::save_visualization(
    const Graph& graph,
    const Step1Data& step1_data,
    const std::string& filepath
) {
    // Convert grayscale to BGR
    cv::Mat vis;
    cv::cvtColor(step1_data.original_map, vis, cv::COLOR_GRAY2BGR);

    // Draw edges (blue)
    cv::Scalar edge_color(255, 0, 0);  // BGR: blue
    auto edges = graph.edges();
    for (const auto& edge : edges) {
        cv::Point p1(edge.first.second, edge.first.first);
        cv::Point p2(edge.second.second, edge.second.first);
        cv::line(vis, p1, p2, edge_color, 1);
    }

    // Draw nodes (red)
    cv::Scalar node_color(0, 0, 255);  // BGR: red
    int node_radius = 2;
    auto nodes = graph.nodes();
    for (const auto& node : nodes) {
        cv::Point p(node.second, node.first);
        cv::circle(vis, p, node_radius, node_color, -1);
    }

    // Save
    cv::imwrite(filepath, vis);
}

void FileWriter::save_all(
    const Graph& graph,
    const Step1Data& step1_data,
    const std::string& output_dir,
    bool save_gml_flag,
    bool save_graphml_flag,
    bool verbose
) {
    // Create output directory
    create_directory(output_dir);

    // Save GML
    if (save_gml_flag) {
        std::string gml_path = output_dir + "/graph.gml";
        try {
            save_gml(graph, gml_path);
            log("GML形式で保存しました: " + gml_path, verbose);
        } catch (const std::exception& e) {
            log("GML保存エラー: " + std::string(e.what()), verbose);
        }
    }

    // Save GraphML
    if (save_graphml_flag) {
        std::string graphml_path = output_dir + "/graph.graphml";
        try {
            save_graphml(graph, graphml_path);
            log("GraphML形式で保存しました: " + graphml_path, verbose);
        } catch (const std::exception& e) {
            log("GraphML保存エラー: " + std::string(e.what()), verbose);
        }
    }

    // Save nodes
    std::string nodes_path = output_dir + "/nodes.txt";
    save_nodes_txt(graph, nodes_path);
    log("ノード座標を保存しました: " + nodes_path, verbose);

    // Save edges
    std::string edges_path = output_dir + "/edges.txt";
    save_edges_txt(graph, edges_path);
    log("エッジ情報を保存しました: " + edges_path, verbose);

    // Save JSON
    std::string json_path = output_dir + "/waypoint_graph.json";
    try {
        save_json(graph, json_path);
        log("JSON形式で保存しました: " + json_path, verbose);
    } catch (const std::exception& e) {
        log("JSON保存エラー: " + std::string(e.what()), verbose);
    }

    // Save visualization
    std::string vis_path = output_dir + "/graph_visualization.png";
    save_visualization(graph, step1_data, vis_path);
    log("可視化を保存しました: " + vis_path, verbose);
}

} // namespace swagger
