#pragma once

#include "graph.hpp"
#include "step1_preprocess.hpp"
#include <string>

namespace swagger {

class FileWriter {
public:
    FileWriter() = default;

    // Save graph in GML format
    static void save_gml(const Graph& graph, const std::string& filepath);

    // Save graph in GraphML format
    static void save_graphml(const Graph& graph, const std::string& filepath);

    // Save nodes as text
    static void save_nodes_txt(const Graph& graph, const std::string& filepath);

    // Save edges as text
    static void save_edges_txt(const Graph& graph, const std::string& filepath);

    // Save graph in JSON format
    static void save_json(const Graph& graph, const std::string& filepath);

    // Save visualization
    static void save_visualization(
        const Graph& graph,
        const Step1Data& step1_data,
        const std::string& filepath
    );

    // Save all results
    static void save_all(
        const Graph& graph,
        const Step1Data& step1_data,
        const std::string& output_dir,
        bool save_gml_flag,
        bool save_graphml_flag,
        bool verbose = true
    );

private:
    static void log(const std::string& message, bool verbose);
    static void create_directory(const std::string& dir_path);
};

} // namespace swagger
