#pragma once

#include "graph.hpp"
#include "utils.hpp"

namespace swagger {

class FreeSpaceSampler {
public:
    // Sample nodes in free space areas
    static void sample_free_space(
        Graph& graph,
        const Step1Data& step1_data,
        double distance_threshold,
        bool verbose = true
    );
};

} // namespace swagger
