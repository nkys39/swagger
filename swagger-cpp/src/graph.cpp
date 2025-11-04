#include "graph.hpp"
#include <stdexcept>
#include <algorithm>

namespace swagger {

void Graph::add_node(const NodeId& node_id, const NodeData& data) {
    nodes_[node_id] = data;
    // Initialize adjacency list entry
    if (adjacency_.find(node_id) == adjacency_.end()) {
        adjacency_[node_id] = std::set<NodeId>();
    }
}

void Graph::add_edge(const NodeId& src, const NodeId& dst, const EdgeData& data) {
    // Add nodes if they don't exist
    if (!has_node(src)) {
        add_node(src);
    }
    if (!has_node(dst)) {
        add_node(dst);
    }

    // Normalize edge (always store src < dst for undirected graph)
    auto edge = src < dst ? std::make_pair(src, dst) : std::make_pair(dst, src);

    // Add edge
    edges_set_.insert(edge);
    edges_[edge] = data;

    // Update adjacency lists
    adjacency_[src].insert(dst);
    adjacency_[dst].insert(src);
}

bool Graph::has_node(const NodeId& node_id) const {
    return nodes_.find(node_id) != nodes_.end();
}

bool Graph::has_edge(const NodeId& src, const NodeId& dst) const {
    auto edge = src < dst ? std::make_pair(src, dst) : std::make_pair(dst, src);
    return edges_set_.find(edge) != edges_set_.end();
}

const NodeData& Graph::get_node_data(const NodeId& node_id) const {
    auto it = nodes_.find(node_id);
    if (it == nodes_.end()) {
        throw std::runtime_error("Node not found");
    }
    return it->second;
}

NodeData& Graph::get_node_data(const NodeId& node_id) {
    auto it = nodes_.find(node_id);
    if (it == nodes_.end()) {
        throw std::runtime_error("Node not found");
    }
    return it->second;
}

const EdgeData& Graph::get_edge_data(const NodeId& src, const NodeId& dst) const {
    auto edge = src < dst ? std::make_pair(src, dst) : std::make_pair(dst, src);
    auto it = edges_.find(edge);
    if (it == edges_.end()) {
        throw std::runtime_error("Edge not found");
    }
    return it->second;
}

EdgeData& Graph::get_edge_data(const NodeId& src, const NodeId& dst) {
    auto edge = src < dst ? std::make_pair(src, dst) : std::make_pair(dst, src);
    auto it = edges_.find(edge);
    if (it == edges_.end()) {
        throw std::runtime_error("Edge not found");
    }
    return it->second;
}

std::vector<NodeId> Graph::neighbors(const NodeId& node_id) const {
    auto it = adjacency_.find(node_id);
    if (it == adjacency_.end()) {
        return std::vector<NodeId>();
    }
    return std::vector<NodeId>(it->second.begin(), it->second.end());
}

std::vector<NodeId> Graph::nodes() const {
    std::vector<NodeId> result;
    result.reserve(nodes_.size());
    for (const auto& pair : nodes_) {
        result.push_back(pair.first);
    }
    return result;
}

std::vector<std::pair<NodeId, NodeId>> Graph::edges() const {
    std::vector<std::pair<NodeId, NodeId>> result;
    result.reserve(edges_.size());
    for (const auto& pair : edges_) {
        result.push_back(pair.first);
    }
    return result;
}

void Graph::clear() {
    nodes_.clear();
    edges_set_.clear();
    edges_.clear();
    adjacency_.clear();
}

} // namespace swagger
