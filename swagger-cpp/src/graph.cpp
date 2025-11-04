#include "graph.hpp"
#include <stdexcept>
#include <algorithm>
#include <queue>

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

void Graph::remove_node(const NodeId& node_id) {
    // Remove all edges connected to this node
    if (adjacency_.find(node_id) != adjacency_.end()) {
        auto neighbors_copy = adjacency_[node_id];
        for (const auto& neighbor : neighbors_copy) {
            remove_edge(node_id, neighbor);
        }
    }

    // Remove node
    nodes_.erase(node_id);
    adjacency_.erase(node_id);
}

void Graph::remove_edge(const NodeId& src, const NodeId& dst) {
    auto edge = src < dst ? std::make_pair(src, dst) : std::make_pair(dst, src);

    edges_set_.erase(edge);
    edges_.erase(edge);

    if (adjacency_.find(src) != adjacency_.end()) {
        adjacency_[src].erase(dst);
    }
    if (adjacency_.find(dst) != adjacency_.end()) {
        adjacency_[dst].erase(src);
    }
}

size_t Graph::degree(const NodeId& node_id) const {
    auto it = adjacency_.find(node_id);
    if (it == adjacency_.end()) {
        return 0;
    }
    return it->second.size();
}

std::vector<std::set<NodeId>> Graph::get_connected_components() const {
    std::set<NodeId> visited;
    std::vector<std::set<NodeId>> components;

    for (const auto& [node_id, _] : nodes_) {
        if (visited.find(node_id) != visited.end()) {
            continue;
        }

        // BFS to find component
        std::set<NodeId> component;
        std::queue<NodeId> queue;
        queue.push(node_id);
        visited.insert(node_id);

        while (!queue.empty()) {
            NodeId current = queue.front();
            queue.pop();
            component.insert(current);

            for (const auto& neighbor : neighbors(current)) {
                if (visited.find(neighbor) == visited.end()) {
                    visited.insert(neighbor);
                    queue.push(neighbor);
                }
            }
        }

        components.push_back(component);
    }

    return components;
}

Graph Graph::get_subgraph(const std::set<NodeId>& nodes_subset) const {
    Graph subgraph;

    // Add nodes
    for (const auto& node : nodes_subset) {
        if (has_node(node)) {
            subgraph.add_node(node, get_node_data(node));
        }
    }

    // Add edges
    for (const auto& node : nodes_subset) {
        for (const auto& neighbor : neighbors(node)) {
            if (nodes_subset.find(neighbor) != nodes_subset.end() && node < neighbor) {
                subgraph.add_edge(node, neighbor, get_edge_data(node, neighbor));
            }
        }
    }

    return subgraph;
}

} // namespace swagger
