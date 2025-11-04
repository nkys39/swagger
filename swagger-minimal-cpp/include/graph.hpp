#pragma once

#include <map>
#include <set>
#include <vector>
#include <string>
#include <utility>
#include <cmath>

namespace swagger {

// Node ID type (row, col)
using NodeId = std::pair<int, int>;

// Node attributes
struct NodeData {
    std::string node_type;

    NodeData() : node_type("unknown") {}
    explicit NodeData(const std::string& type) : node_type(type) {}
};

// Edge attributes
struct EdgeData {
    double weight;
    std::string edge_type;

    EdgeData() : weight(0.0), edge_type("unknown") {}
    EdgeData(double w, const std::string& type) : weight(w), edge_type(type) {}
};

// Graph class
class Graph {
public:
    Graph() = default;

    // Add node
    void add_node(const NodeId& node_id, const NodeData& data = NodeData());

    // Add edge
    void add_edge(const NodeId& src, const NodeId& dst, const EdgeData& data);

    // Check if node exists
    bool has_node(const NodeId& node_id) const;

    // Check if edge exists
    bool has_edge(const NodeId& src, const NodeId& dst) const;

    // Get node data
    const NodeData& get_node_data(const NodeId& node_id) const;
    NodeData& get_node_data(const NodeId& node_id);

    // Get edge data
    const EdgeData& get_edge_data(const NodeId& src, const NodeId& dst) const;
    EdgeData& get_edge_data(const NodeId& src, const NodeId& dst);

    // Get neighbors
    std::vector<NodeId> neighbors(const NodeId& node_id) const;

    // Get all nodes
    std::vector<NodeId> nodes() const;

    // Get all edges
    std::vector<std::pair<NodeId, NodeId>> edges() const;

    // Get number of nodes/edges
    size_t num_nodes() const { return nodes_.size(); }
    size_t num_edges() const { return edges_.size(); }

    // Clear graph
    void clear();

private:
    std::map<NodeId, NodeData> nodes_;
    std::set<std::pair<NodeId, NodeId>> edges_set_;  // For fast lookup
    std::map<std::pair<NodeId, NodeId>, EdgeData> edges_;
    std::map<NodeId, std::set<NodeId>> adjacency_;  // Adjacency list
};

// Utility functions
inline double euclidean_distance(const NodeId& n1, const NodeId& n2) {
    double dy = static_cast<double>(n1.first - n2.first);
    double dx = static_cast<double>(n1.second - n2.second);
    return std::sqrt(dy * dy + dx * dx);
}

} // namespace swagger
