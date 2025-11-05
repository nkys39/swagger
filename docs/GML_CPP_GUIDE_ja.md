# C++でのGML処理ガイド

C++でSWAGGERのGMLファイルを読み込み、処理、可視化する方法を解説します。

## 目次
- [C++グラフライブラリ](#cグラフライブラリ)
- [Boost Graph Library (BGL)](#boost-graph-library-bgl)
- [その他のライブラリ](#その他のライブラリ)
- [可視化方法](#可視化方法)
- [ROS2/Nav2統合](#ros2nav2統合)
- [実践例](#実践例)

---

## C++グラフライブラリ

### 主要ライブラリ比較

| ライブラリ | GML対応 | 学習曲線 | パフォーマンス | 用途 |
|-----------|---------|---------|--------------|------|
| **Boost Graph Library** | ✅ | 高 | ⭐⭐⭐⭐⭐ | 汎用、最も機能豊富 |
| **LEMON** | ✅ | 中 | ⭐⭐⭐⭐⭐ | 最適化、効率重視 |
| **igraph (C API)** | ✅ | 低 | ⭐⭐⭐⭐ | シンプル、Python版もあり |
| **OGDF** | ✅ | 中 | ⭐⭐⭐⭐ | グラフ描画、可視化 |
| **NetworkKit** | ❌ | 中 | ⭐⭐⭐⭐⭐ | 大規模グラフ |

---

## Boost Graph Library (BGL)

最も広く使われているC++グラフライブラリ。強力な機能と柔軟性。

### インストール

```bash
# Ubuntu/Debian
sudo apt-get install libboost-all-dev

# または特定のライブラリのみ
sudo apt-get install libboost-graph-dev
```

### GMLファイルの読み込み

**方法1: Dynamic Propertiesを使用（推奨）**

```cpp
#include <boost/graph/adjacency_list.hpp>
#include <boost/graph/graph_traits.hpp>
#include <boost/property_map/dynamic_property_map.hpp>
#include <boost/graph/graphml.hpp>
#include <fstream>
#include <iostream>

// グラフ型の定義
struct VertexProperties {
    std::string label;
    std::vector<double> world;  // [x, y, z]
    std::vector<int> pixel;     // [row, col]
};

struct EdgeProperties {
    double weight;
    std::string edge_type;
};

typedef boost::adjacency_list<
    boost::vecS,              // OutEdgeList
    boost::vecS,              // VertexList
    boost::undirectedS,       // Directed
    VertexProperties,         // VertexProperties
    EdgeProperties            // EdgeProperties
> Graph;

typedef boost::graph_traits<Graph>::vertex_descriptor Vertex;
typedef boost::graph_traits<Graph>::edge_descriptor Edge;

// GMLパーサー（カスタム実装）
bool loadGML(const std::string& filename, Graph& graph) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Failed to open file: " << filename << std::endl;
        return false;
    }

    // GMLファイルのパース実装
    // 注: Boostには標準のGMLパーサーがないため、カスタム実装が必要

    std::string line;
    bool in_node = false;
    bool in_edge = false;

    Vertex current_vertex;
    std::map<int, Vertex> id_to_vertex;

    int node_id = -1;
    int edge_source = -1;
    int edge_target = -1;

    while (std::getline(file, line)) {
        // Trim whitespace
        line.erase(0, line.find_first_not_of(" \t\n\r\f\v"));
        line.erase(line.find_last_not_of(" \t\n\r\f\v") + 1);

        if (line.find("node [") != std::string::npos) {
            in_node = true;
            current_vertex = boost::add_vertex(graph);
        } else if (line.find("edge [") != std::string::npos) {
            in_edge = true;
        } else if (line == "]") {
            if (in_node) {
                if (node_id >= 0) {
                    id_to_vertex[node_id] = current_vertex;
                }
                in_node = false;
                node_id = -1;
            } else if (in_edge) {
                if (edge_source >= 0 && edge_target >= 0) {
                    auto source_vertex = id_to_vertex[edge_source];
                    auto target_vertex = id_to_vertex[edge_target];
                    boost::add_edge(source_vertex, target_vertex, graph);
                }
                in_edge = false;
                edge_source = -1;
                edge_target = -1;
            }
        } else if (in_node) {
            // Parse node attributes
            if (line.find("id ") != std::string::npos) {
                node_id = std::stoi(line.substr(3));
            } else if (line.find("label ") != std::string::npos) {
                size_t start = line.find('"') + 1;
                size_t end = line.rfind('"');
                graph[current_vertex].label = line.substr(start, end - start);
            } else if (line.find("world ") != std::string::npos) {
                // Parse world coordinates
                std::istringstream iss(line.substr(6));
                double x, y, z;
                if (iss >> x >> y >> z) {
                    graph[current_vertex].world = {x, y, z};
                }
            } else if (line.find("pixel ") != std::string::npos) {
                // Parse pixel coordinates
                std::istringstream iss(line.substr(6));
                int row, col;
                if (iss >> row >> col) {
                    graph[current_vertex].pixel = {row, col};
                }
            }
        } else if (in_edge) {
            // Parse edge attributes
            if (line.find("source ") != std::string::npos) {
                edge_source = std::stoi(line.substr(7));
            } else if (line.find("target ") != std::string::npos) {
                edge_target = std::stoi(line.substr(7));
            } else if (line.find("weight ") != std::string::npos) {
                // Note: エッジプロパティの設定は追加実装が必要
            }
        }
    }

    file.close();
    return true;
}

int main() {
    Graph graph;

    if (!loadGML("output/graph.gml", graph)) {
        return 1;
    }

    std::cout << "Loaded graph with "
              << boost::num_vertices(graph) << " vertices and "
              << boost::num_edges(graph) << " edges" << std::endl;

    // ノードを反復処理
    auto vertices = boost::vertices(graph);
    for (auto it = vertices.first; it != vertices.second; ++it) {
        auto& props = graph[*it];
        std::cout << "Node " << props.label << ": ";
        if (!props.world.empty()) {
            std::cout << "world=(" << props.world[0] << ", "
                      << props.world[1] << ", " << props.world[2] << ")";
        }
        std::cout << std::endl;
    }

    return 0;
}
```

**コンパイル:**
```bash
g++ -std=c++17 -o load_gml load_gml.cpp -lboost_graph
./load_gml
```

---

### 簡易GMLパーサー（ヘッダーオンリー）

より実用的な実装：

```cpp
// gml_parser.hpp
#ifndef GML_PARSER_HPP
#define GML_PARSER_HPP

#include <boost/graph/adjacency_list.hpp>
#include <fstream>
#include <sstream>
#include <map>
#include <vector>
#include <string>

namespace swagger {

struct NodeData {
    int id;
    std::string label;
    std::vector<double> world;
    std::vector<int> pixel;
};

struct EdgeData {
    int source;
    int target;
    double weight;
    std::string edge_type;
};

class GMLParser {
public:
    static bool parse(const std::string& filename,
                     std::vector<NodeData>& nodes,
                     std::vector<EdgeData>& edges) {
        std::ifstream file(filename);
        if (!file.is_open()) return false;

        std::string line;
        NodeData current_node;
        EdgeData current_edge;
        bool in_node = false;
        bool in_edge = false;

        while (std::getline(file, line)) {
            trim(line);

            if (line.find("node [") != std::string::npos) {
                in_node = true;
                current_node = NodeData{};
            } else if (line.find("edge [") != std::string::npos) {
                in_edge = true;
                current_edge = EdgeData{};
            } else if (line == "]") {
                if (in_node) {
                    nodes.push_back(current_node);
                    in_node = false;
                } else if (in_edge) {
                    edges.push_back(current_edge);
                    in_edge = false;
                }
            } else if (in_node) {
                parseNodeAttribute(line, current_node);
            } else if (in_edge) {
                parseEdgeAttribute(line, current_edge);
            }
        }

        return true;
    }

private:
    static void trim(std::string& s) {
        s.erase(0, s.find_first_not_of(" \t\n\r\f\v"));
        s.erase(s.find_last_not_of(" \t\n\r\f\v") + 1);
    }

    static void parseNodeAttribute(const std::string& line, NodeData& node) {
        if (line.find("id ") == 0) {
            node.id = std::stoi(line.substr(3));
        } else if (line.find("label ") == 0) {
            size_t start = line.find('"') + 1;
            size_t end = line.rfind('"');
            node.label = line.substr(start, end - start);
        } else if (line.find("world ") == 0) {
            std::istringstream iss(line.substr(6));
            double x, y, z;
            if (iss >> x >> y >> z) {
                node.world = {x, y, z};
            }
        } else if (line.find("pixel ") == 0) {
            std::istringstream iss(line.substr(6));
            int row, col;
            if (iss >> row >> col) {
                node.pixel = {row, col};
            }
        }
    }

    static void parseEdgeAttribute(const std::string& line, EdgeData& edge) {
        if (line.find("source ") == 0) {
            edge.source = std::stoi(line.substr(7));
        } else if (line.find("target ") == 0) {
            edge.target = std::stoi(line.substr(7));
        } else if (line.find("weight ") == 0) {
            edge.weight = std::stod(line.substr(7));
        } else if (line.find("edge_type ") == 0) {
            size_t start = line.find('"') + 1;
            size_t end = line.rfind('"');
            edge.edge_type = line.substr(start, end - start);
        }
    }
};

} // namespace swagger

#endif // GML_PARSER_HPP
```

**使用例:**

```cpp
#include "gml_parser.hpp"
#include <iostream>

int main() {
    std::vector<swagger::NodeData> nodes;
    std::vector<swagger::EdgeData> edges;

    if (swagger::GMLParser::parse("output/graph.gml", nodes, edges)) {
        std::cout << "Loaded " << nodes.size() << " nodes and "
                  << edges.size() << " edges" << std::endl;

        // ノード情報を表示
        for (const auto& node : nodes) {
            std::cout << "Node " << node.id << " (" << node.label << "): ";
            if (!node.world.empty()) {
                std::cout << "world=(" << node.world[0] << ", "
                          << node.world[1] << ", " << node.world[2] << ")";
            }
            std::cout << std::endl;
        }

        // エッジ情報を表示
        for (const auto& edge : edges) {
            std::cout << "Edge " << edge.source << " -> " << edge.target
                      << " (weight=" << edge.weight
                      << ", type=" << edge.edge_type << ")" << std::endl;
        }
    }

    return 0;
}
```

---

### 経路探索

```cpp
#include <boost/graph/adjacency_list.hpp>
#include <boost/graph/dijkstra_shortest_paths.hpp>
#include <boost/graph/astar_search.hpp>
#include "gml_parser.hpp"

// グラフ型
typedef boost::adjacency_list<
    boost::vecS, boost::vecS, boost::undirectedS,
    swagger::NodeData, boost::property<boost::edge_weight_t, double>
> Graph;

typedef boost::graph_traits<Graph>::vertex_descriptor Vertex;

// A*用のヒューリスティック
class distance_heuristic : public boost::astar_heuristic<Graph, double> {
public:
    distance_heuristic(const Graph& g, Vertex goal)
        : graph_(g), goal_(goal) {}

    double operator()(Vertex v) {
        const auto& v_world = graph_[v].world;
        const auto& goal_world = graph_[goal_].world;

        double dx = v_world[0] - goal_world[0];
        double dy = v_world[1] - goal_world[1];
        return std::sqrt(dx*dx + dy*dy);
    }

private:
    const Graph& graph_;
    Vertex goal_;
};

// 経路探索
std::vector<Vertex> findPath(const Graph& graph, Vertex start, Vertex goal) {
    std::vector<Vertex> predecessors(boost::num_vertices(graph));
    std::vector<double> distances(boost::num_vertices(graph));

    // Dijkstraアルゴリズム
    boost::dijkstra_shortest_paths(
        graph, start,
        boost::predecessor_map(&predecessors[0])
            .distance_map(&distances[0])
            .weight_map(boost::get(boost::edge_weight, graph))
    );

    // パスを再構築
    std::vector<Vertex> path;
    Vertex current = goal;

    while (current != start) {
        path.push_back(current);
        current = predecessors[current];
    }
    path.push_back(start);

    std::reverse(path.begin(), path.end());
    return path;
}

int main() {
    // GMLファイルを読み込み
    std::vector<swagger::NodeData> nodes;
    std::vector<swagger::EdgeData> edges;

    if (!swagger::GMLParser::parse("output/graph.gml", nodes, edges)) {
        return 1;
    }

    // グラフを構築
    Graph graph(nodes.size());

    // ノードプロパティを設定
    for (size_t i = 0; i < nodes.size(); ++i) {
        graph[i] = nodes[i];
    }

    // エッジを追加
    for (const auto& edge : edges) {
        boost::add_edge(edge.source, edge.target, edge.weight, graph);
    }

    // 経路探索
    Vertex start = 0;
    Vertex goal = 10;
    auto path = findPath(graph, start, goal);

    std::cout << "Path from " << start << " to " << goal << ":" << std::endl;
    for (auto v : path) {
        const auto& world = graph[v].world;
        std::cout << "  Node " << v << ": ("
                  << world[0] << ", " << world[1] << ")" << std::endl;
    }

    return 0;
}
```

---

## その他のライブラリ

### 1. LEMON (Library for Efficient Modeling and Optimization in Networks)

**特徴:**
- 効率重視
- 最適化アルゴリズムが豊富
- クリーンなAPI

**インストール:**
```bash
sudo apt-get install liblemon-dev
```

**例:**
```cpp
#include <lemon/list_graph.h>
#include <lemon/lgf_reader.h>

using namespace lemon;

int main() {
    ListGraph graph;
    ListGraph::NodeMap<std::string> label(graph);
    ListGraph::EdgeMap<double> weight(graph);

    // LEMONはGMLを直接サポートしないため、
    // 独自パーサーでLGF形式に変換するか、
    // カスタムローダーが必要

    return 0;
}
```

---

### 2. igraph (C API)

**特徴:**
- シンプルなAPI
- Python版との互換性
- ネットワーク分析機能

**インストール:**
```bash
sudo apt-get install libigraph-dev
```

**例:**
```cpp
#include <igraph/igraph.h>

int main() {
    igraph_t graph;
    FILE* file = fopen("output/graph.gml", "r");

    // GMLファイルを読み込み
    igraph_read_graph_gml(&graph, file);
    fclose(file);

    // グラフ情報を取得
    igraph_integer_t vcount = igraph_vcount(&graph);
    igraph_integer_t ecount = igraph_ecount(&graph);

    printf("Vertices: %d, Edges: %d\n", (int)vcount, (int)ecount);

    // クリーンアップ
    igraph_destroy(&graph);

    return 0;
}
```

**コンパイル:**
```bash
gcc -o igraph_example igraph_example.c -ligraph
```

---

## 可視化方法

### 方法1: Graphvizを使用

**C++からGraphviz DOT形式を生成:**

```cpp
#include <fstream>
#include "gml_parser.hpp"

void exportToDot(const std::vector<swagger::NodeData>& nodes,
                 const std::vector<swagger::EdgeData>& edges,
                 const std::string& filename) {
    std::ofstream out(filename);

    out << "graph G {" << std::endl;
    out << "  layout=neato;" << std::endl;
    out << "  node [shape=circle, fontsize=8];" << std::endl;

    // ノードを出力
    for (const auto& node : nodes) {
        out << "  " << node.id << " [label=\"" << node.label << "\"";
        if (!node.world.empty()) {
            out << ", pos=\"" << node.world[0] << "," << node.world[1] << "!\"";
        }
        out << "];" << std::endl;
    }

    // エッジを出力
    for (const auto& edge : edges) {
        out << "  " << edge.source << " -- " << edge.target;
        out << " [label=\"" << edge.weight << "\"];" << std::endl;
    }

    out << "}" << std::endl;
    out.close();
}

int main() {
    std::vector<swagger::NodeData> nodes;
    std::vector<swagger::EdgeData> edges;

    swagger::GMLParser::parse("output/graph.gml", nodes, edges);
    exportToDot(nodes, edges, "graph.dot");

    // Graphvizで画像生成
    system("neato -Tpng graph.dot -o graph.png");

    return 0;
}
```

---

### 方法2: OpenCVで直接描画

```cpp
#include <opencv2/opencv.hpp>
#include "gml_parser.hpp"

void visualizeGraph(const std::vector<swagger::NodeData>& nodes,
                   const std::vector<swagger::EdgeData>& edges,
                   const std::string& map_image_path,
                   const std::string& output_path) {
    // 元の地図を読み込み
    cv::Mat map = cv::imread(map_image_path, cv::IMREAD_GRAYSCALE);
    cv::Mat viz;
    cv::cvtColor(map, viz, cv::COLOR_GRAY2BGR);

    // エッジを描画
    for (const auto& edge : edges) {
        const auto& src_node = nodes[edge.source];
        const auto& dst_node = nodes[edge.target];

        if (src_node.pixel.size() >= 2 && dst_node.pixel.size() >= 2) {
            cv::Point pt1(src_node.pixel[1], src_node.pixel[0]); // (col, row)
            cv::Point pt2(dst_node.pixel[1], dst_node.pixel[0]);

            cv::Scalar color;
            if (edge.edge_type == "skeleton") {
                color = cv::Scalar(0, 0, 255); // Red
            } else if (edge.edge_type == "boundary") {
                color = cv::Scalar(255, 0, 0); // Blue
            } else if (edge.edge_type == "delaunay") {
                color = cv::Scalar(0, 255, 0); // Green
            } else {
                color = cv::Scalar(128, 128, 128); // Gray
            }

            cv::line(viz, pt1, pt2, color, 1, cv::LINE_AA);
        }
    }

    // ノードを描画
    for (const auto& node : nodes) {
        if (node.pixel.size() >= 2) {
            cv::Point pt(node.pixel[1], node.pixel[0]);
            cv::circle(viz, pt, 2, cv::Scalar(255, 255, 0), -1);
        }
    }

    // 保存
    cv::imwrite(output_path, viz);
    std::cout << "Saved visualization to " << output_path << std::endl;
}

int main() {
    std::vector<swagger::NodeData> nodes;
    std::vector<swagger::EdgeData> edges;

    swagger::GMLParser::parse("output/graph.gml", nodes, edges);
    visualizeGraph(nodes, edges,
                  "maps/carter_warehouse_navigation.png",
                  "graph_cpp_viz.png");

    return 0;
}
```

**コンパイル:**
```bash
g++ -std=c++17 -o visualize visualize.cpp `pkg-config --cflags --libs opencv4`
./visualize
```

---

## ROS2/Nav2統合

### C++ Nav2プラグインでの使用

```cpp
// swagger_planner.hpp
#include <rclcpp/rclcpp.hpp>
#include <nav2_core/global_planner.hpp>
#include <boost/graph/adjacency_list.hpp>
#include "gml_parser.hpp"

namespace swagger_nav2_planner {

class SwaggerPlanner : public nav2_core::GlobalPlanner {
public:
    SwaggerPlanner() = default;
    ~SwaggerPlanner() = default;

    void configure(
        const rclcpp_lifecycle::LifecycleNode::WeakPtr & parent,
        std::string name, std::shared_ptr<tf2_ros::Buffer> tf,
        std::shared_ptr<nav2_costmap_2d::Costmap2DROS> costmap_ros) override;

    void cleanup() override;
    void activate() override;
    void deactivate() override;

    nav_msgs::msg::Path createPlan(
        const geometry_msgs::msg::PoseStamped & start,
        const geometry_msgs::msg::PoseStamped & goal) override;

private:
    bool loadGraph(const std::string& gml_path);
    std::vector<int> findPath(int start_node, int goal_node);
    int findNearestNode(double x, double y);

    // グラフデータ
    std::vector<swagger::NodeData> nodes_;
    std::vector<swagger::EdgeData> edges_;

    // ROS
    rclcpp_lifecycle::LifecycleNode::WeakPtr node_;
    std::string global_frame_;
};

} // namespace swagger_nav2_planner
```

---

## 実践例: 完全なプロジェクト

### CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.10)
project(swagger_cpp_example)

set(CMAKE_CXX_STANDARD 17)

# Boost
find_package(Boost REQUIRED COMPONENTS graph)

# OpenCV (オプション)
find_package(OpenCV REQUIRED)

# 実行ファイル
add_executable(load_gml src/load_gml.cpp)
target_include_directories(load_gml PRIVATE include)
target_link_libraries(load_gml ${Boost_LIBRARIES})

add_executable(visualize src/visualize.cpp)
target_include_directories(visualize PRIVATE include)
target_link_libraries(visualize ${OpenCV_LIBS})

add_executable(pathfinder src/pathfinder.cpp)
target_include_directories(pathfinder PRIVATE include)
target_link_libraries(pathfinder ${Boost_LIBRARIES})
```

### ディレクトリ構造

```
swagger_cpp_example/
├── CMakeLists.txt
├── include/
│   └── gml_parser.hpp
├── src/
│   ├── load_gml.cpp
│   ├── visualize.cpp
│   └── pathfinder.cpp
└── README.md
```

### ビルドと実行

```bash
mkdir build && cd build
cmake ..
make

# GMLファイルを読み込み
./load_gml ../output/graph.gml

# 可視化
./visualize ../output/graph.gml ../maps/warehouse.png

# 経路探索
./pathfinder ../output/graph.gml 0 100
```

---

## まとめ

### C++でのGML処理の選択肢

| 要件 | 推奨ライブラリ |
|------|---------------|
| **汎用グラフ処理** | Boost Graph Library |
| **最適化重視** | LEMON |
| **シンプルなAPI** | igraph (C API) |
| **可視化** | OpenCV + カスタム描画 |
| **ROS2統合** | Boost + Nav2 |

### 実装のポイント

1. **GMLパーサー**: Boostは標準のGMLパーサーを持たないため、カスタム実装が必要
2. **座標系**: ピクセル座標とワールド座標の両方を保持
3. **経路探索**: Dijkstra/A*アルゴリズムを使用
4. **可視化**: OpenCVまたはGraphvizを使用
5. **ROS2統合**: Nav2プラグインとして実装

C++での実装は柔軟性とパフォーマンスを提供しますが、Pythonよりも実装コストが高くなります。用途に応じて選択してください。
