#pragma once

#include "graph.hpp"
#include "utils.hpp"

namespace swagger {

class DelaunayShortcuts {
public:
    // Add shortcuts based on Delaunay triangulation
    static void add_delaunay_shortcuts(
        Graph& graph,
        const Step1Data& step1_data,
        bool verbose = true
    );
};

} // namespace swagger
