#pragma once

#include "graph.hpp"
#include "utils.hpp"

namespace swagger {

class GraphPruner {
public:
    // Prune graph: merge close nodes and remove small subgraphs
    static void prune_graph(
        Graph& graph,
        const Step1Data& step1_data,
        double merge_distance,
        double min_subgraph_length,
        bool verbose = true
    );

    // Convert to world coordinates
    static void to_world_coordinates(
        Graph& graph,
        const Step1Data& step1_data
    );
};

} // namespace swagger
