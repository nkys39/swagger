#include "step6_prune.hpp"
#include "utils.hpp"
#include <iostream>
#include <cmath>

namespace swagger {

void GraphPruner::prune_graph(
    Graph& graph,
    double merge_distance,
    double min_subgraph_length,
    bool verbose
) {
    if (verbose) {
        std::cout << "Step 6: グラフ刈り込み (実装中)" << std::endl;
    }

    // TODO: Implement graph pruning
    // Algorithm:
    // 1. Merge nearby nodes (within merge_distance)
    // 2. Find connected components
    // 3. Remove small components (total edge length < min_subgraph_length)

    // Placeholder implementation
    std::cout << "Step6: Graph pruning (placeholder)" << std::endl;
}

void GraphPruner::to_world_coordinates(
    Graph& graph,
    const Step1Data& step1_data
) {
    std::cout << "Step6: Converting to world coordinates (placeholder)" << std::endl;

    // TODO: Convert all node coordinates from pixel to world
    // For each node:
    //   WorldCoord world = pixel_to_world(node_id, step1_data.resolution, ...)
    //   Set node.world = world
}

} // namespace swagger
