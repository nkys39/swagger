#pragma once

#include "graph.hpp"
#include <string>

namespace swagger {

/**
 * @brief Load skeleton nodes from JSON file (exported from Python)
 *
 * This allows using Python's skimage+skan skeleton generation
 * while using C++ for the rest of the pipeline.
 */
class SkeletonLoader {
public:
    /**
     * @brief Load skeleton graph from JSON file
     *
     * @param graph Graph to populate with skeleton nodes
     * @param json_path Path to JSON file
     * @param verbose Enable verbose logging
     * @return true if successful, false otherwise
     */
    static bool load_from_json(
        Graph& graph,
        const std::string& json_path,
        bool verbose = false
    );

private:
    static void log(const std::string& message, bool verbose);
};

} // namespace swagger
