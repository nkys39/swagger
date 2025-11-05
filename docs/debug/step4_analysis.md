# Step 4 Free Space Sampling: 詳細分析

## 発見した問題

### 問題1: 矩形範囲 vs 円形範囲

**Python (R-tree):**
```python
bounding_box = (col - half_threshold, row - half_threshold,
                col + half_threshold, row + half_threshold)
intersections = list(idx.intersection(bounding_box))
```
→ **矩形範囲** での近接ノード検索

**C++ (KD-tree):**
```cpp
kdtree.radiusSearch(query, indices, dists,
                    half_threshold * half_threshold, ...)
```
→ **円形範囲** での近接ノード検索

**影響:**
- 矩形の角では、円よりも遠いノード（距離 ≤ half_threshold * √2）も検出
- half_threshold = 15px の場合:
  - 円形: 距離 ≤ 15px
  - 矩形: 距離 ≤ 21.2px (角の場合)
- Pythonの方が広範囲を検索 → より多くノードを除外 → 少ないノードを追加

---

### 問題2: 同一反復内でのノード追加の扱い（**重大**）

**Python:**
```python
for coord in local_maxima_coords:
    row, col = coord
    intersections = list(idx.intersection(bounding_box))
    if len(intersections) == 0:
        graph.add_node((row, col), node_type="free_space")
        idx.insert(len(graph.nodes) - 1, (col, row, col, row))  # ← R-treeに即座に追加！
        distance_map[row, col] = 0
```
→ 新しく追加したノードを**即座にR-treeに追加**
→ 同じ反復内の後続のlocal maximaをチェックする際、**既に追加したノードも考慮される**

**C++:**
```cpp
// KD-treeは反復の最初に一度だけ構築
cv::flann::Index kdtree(node_coords, ...);

for (const auto& point : local_maxima) {
    int num_found = kdtree.radiusSearch(...);  // ← 同じKD-treeを使い回し
    if (num_found == 0) {
        graph.add_node(candidate, NodeData("free_space"));
        distance_map.at<float>(point.y, point.x) = 0.0f;
        nodes_added_this_iter++;  // ← KD-treeは更新されない！
    }
}
```
→ KD-treeは反復中に更新されない
→ 同じ反復内で追加された新しいノードは、**後続のlocal maximaのチェックで考慮されない**

**影響:**
同じ反復内で複数のlocal maximaが近接している場合：
- **Python:** 最初のノードを追加した後、それに近い後続のノードは追加されない
- **C++:** すべてのlocal maximaが互いを考慮せずに追加される可能性がある

これが**大量のノードが密集して追加される原因**です！

---

### 問題3: 最大反復数の違い

**Python:**
```python
while True:  # 無限ループ、収束するまで反復
```

**C++:**
```cpp
int max_iterations = 20;
while (iteration < max_iterations) {
```

Pythonは収束するまで反復しますが、C++は最大20反復で停止します。

---

## 解決策

### 修正1: 矩形範囲検索に変更

C++でもR-treeのような矩形範囲検索を実装するか、または円形範囲の半径を調整：
```cpp
// 矩形の対角線に合わせて半径を拡大
double search_radius = half_threshold * 1.414;  // sqrt(2)
```

### 修正2: 同一反復内でのノード追加を追跡（重要）

```cpp
// この反復で追加されたノードを追跡
std::vector<cv::Point> nodes_added_in_this_iter;

for (const auto& point : local_maxima) {
    // 既存ノード + この反復で追加したノードをチェック
    bool too_close = false;

    // 既存ノードとの距離チェック（KD-tree）
    int num_found = kdtree.radiusSearch(...);
    if (num_found > 0) {
        too_close = true;
    }

    // この反復で追加したノードとの距離チェック
    if (!too_close) {
        for (const auto& added : nodes_added_in_this_iter) {
            double dist = cv::norm(point - added);
            if (dist < half_threshold) {
                too_close = true;
                break;
            }
        }
    }

    if (!too_close) {
        graph.add_node(candidate, NodeData("free_space"));
        distance_map.at<float>(point.y, point.x) = 0.0f;
        nodes_added_in_this_iter.push_back(point);
    }
}
```

### 修正3: 最大反復数を削除

```cpp
while (true) {  // Pythonと同じく無限ループ
    // 収束条件でbreak
}
```
