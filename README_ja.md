# SWAGGER 日本語ガイド

**SWAGGER (Sparse WAypoint Graph Generation for Efficient Routing)** の詳細な日本語解説ドキュメントです。

> **注意**: このドキュメントは、CPU専用版（CUDA依存を削除したフォーク版）に基づいています。オリジナルのNVIDIA版はCUDA/GPU環境が必要です。

## 目次

- [概要](#概要)
- [リポジトリの使い方](#リポジトリの使い方)
- [アルゴリズムの詳細](#アルゴリズムの詳細)
- [境界検出の詳細](#境界検出の詳細)
- [処理負荷ランキング](#処理負荷ランキング)
- [グラフ評価基準](#グラフ評価基準)
- [Git LFSについて](#git-lfsについて)
- [CPU版について](#cpu版について)
- [GML形式とNav2統合](GML_AND_NAV2_INTEGRATION_ja.md) - 出力形式とROS2統合の詳細
- [GML可視化ツールガイド](GML_VISUALIZATION_TOOLS_ja.md) - グラフを可視化する各種ツールの使い方
- [C++でのGML処理](GML_CPP_GUIDE_ja.md) - C++でGMLファイルを読み込み・処理・可視化する方法
- [グラフデータ形式ガイド](GRAPH_FORMATS_GUIDE_ja.md) - GML、GraphML、DOT、JSON等の形式比較
- [モジュラー実行ガイド](MODULAR_USAGE.md) - 各ステップを個別に実行する方法

---

## 概要

**SWAGGER** は、占有グリッドマップから経路計画用のスパースなウェイポイントグラフを生成するPythonパッケージです。NVIDIAが開発しており、ロボットナビゲーション向けに最適化されています。

### リポジトリのバージョンについて

| バージョン | リポジトリ | CUDA要件 | 特徴 |
|----------|-----------|---------|------|
| **オリジナル版** | [nvidia-isaac/SWAGGER](https://github.com/nvidia-isaac/SWAGGER) | **必須** (CUDA 12.5+) | GPU高速化あり |
| **CPU専用版（このフォーク）** | [nkys39/swagger](https://github.com/nkys39/swagger) | **不要** | CPU環境で動作 |

### 主な特徴

- 占有グリッドマップから効率的なウェイポイントグラフを自動生成
- スケルトン（medial axis）ベースのグラフ構築
- 境界サンプリングによる障害物付近のカバレッジ改善
- 自由空間の効率的なサンプリング
- Delaunay三角分割によるショートカット追加
- **CPU環境で動作（CUDA不要）** ※このフォークのみ

---

## リポジトリの使い方

### システム要件

#### オリジナル版（NVIDIA公式）
- Python 3.10以降
- Linux (Ubuntu 22.04推奨)
- **CUDA 12.5以降** + NVIDIA CUDA toolkit

#### CPU専用版（このフォーク）
- Python 3.10以降
- Linux (Ubuntu 22.04推奨)
- **CUDA不要**

### インストール

#### 前提条件

システムパッケージのインストール：
```bash
sudo apt update && sudo apt install -y libgl1-mesa-glx libglib2.0-0
```

#### 方法1: uvを使う（推奨 - 高速！）

[uv](https://github.com/astral-sh/uv) は高速なPythonパッケージインストーラーです。

```bash
# uvをインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# リポジトリをクローン
git clone git@github.com:nkys39/swagger.git
cd swagger
git lfs pull  # オプション: サンプルマップを使う場合のみ

# 仮想環境を作成してインストール
uv venv
source .venv/bin/activate
uv pip install -e .
```

#### 方法2: pip/venvを使う（従来の方法）

```bash
# リポジトリをクローン
git clone git@github.com:nkys39/swagger.git
cd swagger
git lfs pull  # オプション: サンプルマップを使う場合のみ

# 仮想環境を作成してアクティベート
python -m venv swagger-venv
source swagger-venv/bin/activate

# パッケージをインストール
pip install -e .
```

#### オリジナル版（GPU版）のインストール

オリジナル版を使用する場合は、[公式リポジトリのREADME](https://github.com/nvidia-isaac/SWAGGER)を参照してください。CUDA環境のセットアップが必要です。

### 基本的な使い方

#### コマンドラインから

```bash
python scripts/generate_graph.py \
    --map-path maps/carter_warehouse_navigation.png \
    --resolution 0.05 \
    --safety-distance 0.3 \
    --output-dir output
```

**パラメータ:**
- `--map-path`: 占有グリッドマップのパス（0=障害物、255=自由空間）
- `--resolution`: 解像度（メートル/ピクセル）
- `--safety-distance`: ロボットの安全距離（メートル）
- `--output-dir`: 出力ディレクトリ

**出力:**
- `waypoint_graph.png`: グラフの可視化画像
- `graph.gml`: GML形式のグラフデータ

#### モジュラー実行

グラフ生成処理をより細かく制御したい場合、各アルゴリズムステップを個別に実行できます。これは以下の場合に便利です：
- 特定のステップのデバッグ
- 異なるパラメータの組み合わせで実験
- 中間結果の可視化
- 必要なステップのみを実行

詳細は [MODULAR_USAGE.md](MODULAR_USAGE.md) を参照してください：
- パイプライン全体の実行
- 特定のステップのみ実行
- 一部のステップをスキップ
- 各ステップの出力を可視化
- 各ステップのパラメータ調整

クイック例：
```bash
# 全ステップを可視化付きで実行
python scripts/run_pipeline.py \
    --map maps/carter_warehouse_navigation.png \
    --output output/ \
    --visualize-all

# スケルトンと境界のステップのみ実行
python scripts/run_pipeline.py \
    --map maps/carter_warehouse_navigation.png \
    --output output/ \
    --steps 1,2,3,6
```

#### Pythonコードから

```python
import cv2
from swagger import WaypointGraphGenerator
from swagger.models import Point

# マップの読み込み
occupancy_grid = cv2.imread("map.png", cv2.IMREAD_GRAYSCALE)

# グラフジェネレータの作成
generator = WaypointGraphGenerator()

# グラフの生成
graph = generator.build_graph_from_grid_map(
    image=occupancy_grid,
    resolution=0.05,           # メートル/ピクセル
    safety_distance=0.3,       # ロボットの安全距離(メートル)
    occupancy_threshold=127,   # 占有判定の閾値
    x_offset=0.0,             # X座標オフセット
    y_offset=0.0,             # Y座標オフセット
    rotation=0.0              # 回転角度（ラジアン）
)

# 経路探索
start = Point(x=13.0, y=18.0)
goal = Point(x=15.0, y=10.0)
route = generator.find_route(start, goal)

# 可視化
generator.visualize_graph(output_dir="output")
```

#### REST API

```bash
# REST APIサーバーを起動
python scripts/rest_api.py

# または Dockerで起動
cd docker
docker compose up rest-api
```

APIドキュメント: `http://localhost:8000/v1/docs`

### パラメータ調整

グラフ生成パラメータをカスタマイズできます：

```python
from swagger import WaypointGraphGenerator, WaypointGraphGeneratorConfig

config = WaypointGraphGeneratorConfig(
    skeleton_sample_distance=1.0,        # スケルトンサンプリング間隔(m)
    boundary_inflation_factor=2.0,       # 境界膨張率
    boundary_sample_distance=1.5,        # 境界サンプリング間隔(m)
    free_space_sampling_threshold=2.0,   # 自由空間サンプリング閾値(m)
    merge_node_distance=0.3,             # ノードマージ距離(m)
    min_subgraph_length=1.0,             # 最小サブグラフ長(m)
    use_skeleton_graph=True,             # スケルトングラフを使用
    use_boundary_sampling=True,          # 境界サンプリングを使用
    use_free_space_sampling=True,        # 自由空間サンプリングを使用
    use_delaunay_shortcuts=True,         # Delaunayショートカットを使用
    prune_graph=True                     # グラフ剪定を実行
)

generator = WaypointGraphGenerator(config=config)
```

---

## アルゴリズムの詳細

アルゴリズムは**6つの主要ステップ**で構成されています：

### ステップ1: 安全バッファの追加

**実装**: `_distance_transform()` (waypoint_graph_generator.py:272)

```python
def _distance_transform(self, free_map: np.ndarray):
    # マップの周囲に1ピクセルのパディングを追加
    free_map = np.pad(free_map, ((1, 1), (1, 1)), mode="constant", constant_values=0)

    # 距離変換を計算（各自由空間ピクセルから最も近い障害物までの距離）
    self._dist_transform = cv2.distanceTransform(free_map, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)

    # ロボットの安全距離内のピクセルを障害物としてマーク
    self._inflated_map = (self._dist_transform < self._safety_distance / self._resolution).astype(np.uint8)
```

**処理内容:**
- OpenCVの精密距離変換（`DIST_MASK_PRECISE`）を使用
- 各自由空間ピクセルから最も近い障害物までのユークリッド距離を計算
- ロボットの安全距離（`safety_distance`）内のピクセルを障害物としてマーク
- マップのエッジにノードが作成されないよう、1ピクセルのパディングを追加

### ステップ2: スケルトングラフの構築

**実装**: `_build_graph_from_skeleton()` (waypoint_graph_generator.py:355)

```python
def _build_graph_from_skeleton(self, skeleton_sample_distance: int):
    # skimage（CPU版）を使用して骨格画像を生成
    skeleton_image = skeletonize(1 - self._inflated_map)

    # skanライブラリでスケルトンを分析
    skeleton = skan.Skeleton(skeleton_image)
    graph = nx.Graph()

    # 各分岐（パス）を処理
    for i in range(skeleton.n_paths):
        branch = skeleton.path_coordinates(i)
        num_segments = max(1, len(branch) // skeleton_sample_distance)
        segment_length = len(branch) // num_segments

        for j in range(num_segments):
            start = branch[j * segment_length]
            end = branch[min((j + 1) * segment_length, len(branch) - 1)]
            if not self._check_line_collision(start, end):
                dist = np.linalg.norm(end - start)
                graph.add_edge((start[0], start[1]), (end[0], end[1]),
                             weight=dist, edge_type="skeleton")
```

**処理内容:**
- 細線化アルゴリズムで自由空間のmedial axis（中心軸）を抽出
- skanライブラリでスケルトンの分岐構造を分析
- 各分岐を`skeleton_sample_distance`間隔でサンプリング
- 連続するノード間にエッジを追加
- Bresenhamアルゴリズムで衝突チェック

### ステップ3: 境界ノードの作成

**実装**: `_sample_obstacle_boundaries()` (waypoint_graph_generator.py:523)

このステップは障害物付近のカバレッジを改善するための重要な処理です。

#### 3-1. 輪郭の検出

**実装**: `_find_obstacle_contours()` (waypoint_graph_generator.py:573)

```python
def _find_obstacle_contours(self, boundary_inflation: float):
    # 距離変換を使用して障害物を特定
    # boundary_inflation = boundary_inflation_factor × safety_distance
    filtered_obstacles = (self._dist_transform >= boundary_inflation).astype(np.uint8)

    # OpenCVで輪郭を検出
    contours, _ = cv2.findContours(filtered_obstacles, cv2.RETR_LIST, cv2.CHAIN_APPROX_TC89_KCOS)
    return contours
```

**処理内容:**
- `boundary_inflation_factor`（デフォルト1.5）× 安全距離で障害物を膨張
- 距離変換マップを使用して膨張した障害物領域を特定
- OpenCVの`findContours()`で輪郭を抽出
- `CHAIN_APPROX_TC89_KCOS`: Teh-Chinチェーン近似アルゴリズム（効率的な輪郭近似）

**重要ポイント:**
- 輪郭は安全距離よりも**外側**（1.5倍の位置）で検出
- これにより、障害物の近くでもロボットが安全に移動できる経路を確保

#### 3-2. 境界サンプリング

```python
def _sample_obstacle_boundaries(self, graph: nx.Graph, sample_distance: float = 50):
    contours = self._find_obstacle_contours(
        self._config.boundary_inflation_factor * self._safety_distance / self._resolution
    )

    for contour in contours:
        contour_nodes = []

        # 輪郭の各頂点を処理
        for i in range(len(contour)):
            p1 = contour[i][0]
            p2 = contour[(i + 1) % len(contour)][0]  # 次の点（ループ）

            # 頂点をノードとして追加
            row_1, col_1 = int(p1[1]), int(p1[0])
            contour_nodes.append((row_1, col_1))
            graph.add_node((row_1, col_1), node_type="boundary")

            # 頂点間の距離を計算
            segment_length = np.linalg.norm(p2 - p1)
            num_intermediate = int(segment_length / sample_distance)

            # 中間点を補間
            intermediate_points = np.linspace(p1, p2, num=num_intermediate, endpoint=False).astype(int).tolist()[1:]
            for point in intermediate_points:
                col, row = point
                contour_nodes.append((row, col))
                graph.add_node((row, col), node_type="boundary")

        # 連続するノード間をエッジで接続
        self._connect_contour_nodes(contour_nodes, graph)
```

**処理内容:**
- 各輪郭に沿って`boundary_sample_distance`（デフォルト2.5m）間隔でノードを配置
- 輪郭の頂点間の距離を計算し、必要に応じて中間点を線形補間
- 連続するノード間をエッジで接続
- 衝突チェックを実行して無効なエッジを除外

**境界検出の効果:**
- 障害物付近での経路選択肢が増加
- 狭い通路での経路品質が向上
- 障害物に沿った移動が必要な場合に有効

### ステップ4: 自由空間のノード配置

**実装**: `_sample_free_space()` (waypoint_graph_generator.py:430)

```python
def _sample_free_space(self, graph, distance_threshold: float):
    # 距離マップを初期化（無限大）
    distance_map = np.full(self._original_map.shape, np.inf, dtype=np.float64)

    # 障害物と既存ノードを0に設定
    distance_map[self._original_map <= self._occupancy_threshold] = 0
    for node in graph.nodes():
        row, col = node
        distance_map[row, col] = 0

    # R-tree空間インデックスを初期化
    idx = index.Index()

    # 反復的にノードを追加
    while True:
        # 最も近いノードまでの距離を計算
        distance_map = cv2.distanceTransform(
            (distance_map > 0).astype(np.uint8), cv2.DIST_L2, cv2.DIST_MASK_PRECISE
        )

        # 閾値以上の距離を持つ領域を特定
        large_distance_areas = (distance_map > distance_threshold).astype(np.uint8)
        if not np.any(large_distance_areas):
            break  # これ以上大きな空白領域がない

        # 局所最大値を検出
        dilated = cv2.dilate(distance_map, kernel)
        local_maxima_mask = (distance_map == dilated) & (large_distance_areas > 0)
        local_maxima_coords = np.column_stack(np.where(local_maxima_mask))

        # 局所最大値をノードとして追加
        for coord in local_maxima_coords:
            row, col = coord
            # R-treeで近傍ノードをチェック
            half_threshold = distance_threshold / 2
            bounding_box = (col - half_threshold, row - half_threshold,
                          col + half_threshold, row + half_threshold)
            intersections = list(idx.intersection(bounding_box))
            if len(intersections) == 0:
                graph.add_node((row, col))
                idx.insert(len(graph.nodes) - 1, (col, row, col, row))
                distance_map[row, col] = 0
```

**処理内容:**
- 既存ノードからの距離変換を反復的に計算
- `free_space_sampling_threshold`以上離れた領域を特定
- 膨張処理で局所最大値を検出
- R-tree空間インデックスで効率的な近傍検索
- 適切な局所最大値が見つからなくなるまで反復

**効果:**
- 広い自由空間でのカバレッジ向上
- ノードが均等に分散

### ステップ5: 三角分割とエッジ追加

**実装**: `_add_delaunay_shortcuts()` (waypoint_graph_generator.py:487)

```python
def _add_delaunay_shortcuts(self, graph: nx.Graph):
    nodes = list(graph.nodes())
    if len(nodes) < 3:
        return

    # Delaunay三角分割を計算
    node_coords = np.array(nodes)
    tri = Delaunay(node_coords)

    # 三角形のエッジを収集
    edge_candidates = set()
    for simplex in tri.simplices:
        for i in range(3):
            n1, n2 = tuple(sorted([nodes[simplex[i]], nodes[simplex[(i + 1) % 3]]]))
            if not graph.has_edge(n1, n2):
                edge_candidates.add((n1, n2))

    # 衝突チェックして有効なエッジを追加
    for n1, n2 in edge_candidates:
        if not self._check_line_collision(n1, n2):
            dist = np.sqrt((n2[0] - n1[0]) ** 2 + (n2[1] - n1[1]) ** 2)
            graph.add_edge(n1, n2, weight=dist, edge_type="delaunay")
```

**処理内容:**
- SciPyのDelaunay三角分割でノード間の最適な接続を計算
- 各三角形の3辺を候補エッジとして収集
- Bresenhamアルゴリズムで衝突チェック
- 有効なエッジのみを追加

**効果:**
- 直接的なショートカットを作成
- 経路長を短縮
- グラフの接続性向上

### ステップ6: グラフの剪定

**実装**: `_prune_graph()` (waypoint_graph_generator.py:600)

```python
def _prune_graph(self, graph: nx.Graph):
    # 近接ノードをマージ
    self._merge_close_nodes(graph, threshold=self._to_pixels_int(self._config.merge_node_distance))

    # 孤立ノードを削除
    graph.remove_nodes_from(list(nx.isolates(graph)))

    # 小規模サブグラフを削除
    components = list(nx.connected_components(graph))
    for component in components:
        subgraph = graph.subgraph(component)
        total_length = sum(d["weight"] for _, _, d in subgraph.edges(data=True))
        if total_length < self._to_pixels_int(self._config.min_subgraph_length):
            graph.remove_nodes_from(component)
```

**ノードマージの詳細**: `_merge_close_nodes()` (waypoint_graph_generator.py:619)

```python
def _merge_close_nodes(self, graph: nx.Graph, threshold: float):
    while True:
        nodes = list(graph.nodes())
        node_coords = np.array(nodes)

        # cKDTreeで近接ノードペアを検出
        tree = cKDTree(node_coords)
        pairs = tree.query_pairs(r=threshold)

        if not pairs:
            break  # マージ可能なノードがない

        merged = False
        for n1_idx, n2_idx in pairs:
            n1 = nodes[n1_idx]
            n2 = nodes[n2_idx]

            if not graph.has_node(n2):
                continue

            # n2の全隣接ノードがn1と衝突なく接続できるかチェック
            neighbors = [n for n in graph.neighbors(n2) if n != n1]
            collision = False
            for dst in neighbors:
                if self._check_line_collision(n1, dst):
                    collision = True
                    break

            # 衝突がなければマージ
            if not collision:
                for neighbor in neighbors:
                    dist = np.sqrt((neighbor[0] - n1[0]) ** 2 + (neighbor[1] - n1[1]) ** 2)
                    graph.add_edge(n1, neighbor, weight=dist, edge_type="merge")
                graph.remove_node(n2)
                merged = True

        if not merged:
            break
```

**処理内容:**
- cKDTreeで`merge_node_distance`以内のノードペアを効率的に検出
- 衝突チェックを行い、安全にマージ可能なノードのみ統合
- 孤立ノードと小規模サブグラフを削除
- 反復的に処理（マージ不可能になるまで）

**効果:**
- 冗長なノードを削減
- グラフをクリーンアップ
- 計算効率向上

---

## 処理負荷ランキング

アルゴリズム全体での計算複雑度順のランキング：

### 🥇 第1位: 自由空間サンプリング (`_sample_free_space()`)

**時間複雑度**: O(k × N) ※ k=イテレーション回数、N=ピクセル数

**理由:**
- 距離変換を**反復的に**実行（各イテレーションでO(N)）
- 局所最大値の検出と膨張処理
- R-tree空間インデックスの更新
- 大きなマップでは何百回ものイテレーションが必要

**ボトルネックになる条件:**
- 大きなマップサイズ（例: 2000×2000ピクセル以上）
- 小さい`free_space_sampling_threshold`（密なサンプリング）
- 広い自由空間領域

**最適化方法:**
- `free_space_sampling_threshold`を大きくする
- R-treeインデックスの効率的な利用

### 🥈 第2位: 最近傍ノードマップの構築 (`_build_nearest_node_map()`)

**時間複雑度**: O(N × M × V) ※ N=高さ、M=幅、V=ノード数

**理由:**
- Numbaでコンパイルされたフラッドフィル実装
- マップ全体を走査（O(N × M)）
- BFS風のアプローチで各ピクセルを処理
- グラフ構築後と評価前の両方で実行

**ボトルネックになる条件:**
- 大きなマップサイズ
- 多数のノード（1000+）

**最適化方法:**
- Numba JITコンパイルによる高速化（既に実装済み）
- フラッドフィル実装: waypoint_graph_generator.py:742-763

### 🥉 第3位: 距離変換 (`_distance_transform()`)

**時間複雑度**: O(N × M)

**理由:**
- OpenCVの精密距離変換（`DIST_MASK_PRECISE`）を使用
- マップ全体を処理
- ステップ1で1回、評価中に複数回実行

**ボトルネックになる条件:**
- 非常に大きなマップ
- 評価で複数回実行される場合

**最適化方法:**
- 既にOpenCVの最適化実装を使用
- 必要な場合のみ実行

### 第4位: Delaunay三角分割 (`_add_delaunay_shortcuts()`)

**時間複雑度**: O(V log V + E) ※ V=ノード数、E=候補エッジ数

**理由:**
- ScipyのDelaunay実装（効率的なアルゴリズム）
- すべてのノード座標を処理
- 各候補エッジの衝突チェック（Bresenhamアルゴリズム）

**ボトルネックになる条件:**
- 多数のノード（1000+）
- 密なグラフ

**最適化方法:**
- バッチ処理で候補エッジを収集（既に実装済み）
- 衝突チェックの早期終了

### 第5位: スケルトングラフ構築 (`_build_graph_from_skeleton()`)

**時間複雑度**: O(N × M + B × L) ※ B=分岐数、L=平均分岐長

**理由:**
- scikit-imageによる画像細線化（CPU版）
- skanによるスケルトン分析
- 各分岐の衝突チェック

**ボトルネックになる条件:**
- 複雑な環境（多数の分岐）
- CPU版（GPU版より遅い）

**最適化方法:**
- 細線化アルゴリズムは既に最適化済み
- GPU版（cucim）を使用する場合はさらに高速化可能

### 第6位: 境界サンプリング (`_sample_obstacle_boundaries()`)

**時間複雑度**: O(C × P) ※ C=輪郭数、P=輪郭あたりのポイント数

**理由:**
- 輪郭検出は比較的高速
- 輪郭の長さに比例してノードを追加
- 通常、障害物の輪郭はマップ全体より小さい

**ボトルネックになる条件:**
- 多数の小さな障害物
- 小さい`boundary_sample_distance`

**最適化方法:**
- OpenCVの効率的な輪郭検出を使用（既に実装済み）

### 第7位: グラフ評価 (`evaluate_all()`)

**時間複雑度**: O(N × M + S × (V log V)) ※ S=サンプル数

**理由:**
- カバレッジ指標は距離変換を使用
- 経路指標は1000個のランダムサンプルでA*を実行
- 検証は比較的高速

**ボトルネックになる条件:**
- 大きなマップ
- 多数の経路サンプル

### 第8位: グラフ剪定 (`_prune_graph()`)

**時間複雑度**: O(k × V log V) ※ kは小さい定数

**理由:**
- cKDTreeクエリは効率的（O(log V)）
- 反復的だが通常は少数のイテレーション
- マージ可能なノードが少なくなると早期終了

**最適化方法:**
- cKDTree空間インデックスの使用（既に実装済み）

### パフォーマンス最適化のまとめ

実装済みの最適化:
1. **R-tree/cKDTree**: 空間インデックスによる高速な近傍検索
2. **Numba JIT**: フラッドフィルアルゴリズムのコンパイル
3. **OpenCV**: 距離変換と輪郭検出の最適化実装
4. **早期終了**: 衝突チェックで衝突検出時に即座に返す
5. **バッチ処理**: Delaunay三角分割でのエッジ候補の一括処理

---

## グラフ評価基準

グラフの「良さ」は**用途によって異なります**が、各指標の理想値とトレードオフを説明します。

### 1. カバレッジ指標（Coverage Metrics）

実装: `calculate_coverage_metrics()` (graph_evaluator.py:88)

#### Free Space Coverage（自由空間カバレッジ）

**理想値**: 90%以上

**意味**: ロボットが到達可能な領域の割合

**判断基準**:
- ✅ **95-100%**: 優秀 - ほぼ全域にアクセス可能
- ⚠️ **70-90%**: 許容範囲 - 一部孤立領域あり
- ❌ **70%未満**: 問題あり - 多くの領域が到達不可能

**計算方法**:
```python
# 連結成分分析で各自由空間領域を検出
num_labels, labels, _, _ = cv2.connectedComponentsWithStats(free_space_mask, connectivity=8)

# 各領域にノードがあるかチェック
for label in range(1, num_labels):
    region_mask = labels == label
    has_nodes = np.any(node_image[region_mask] > 0)
    if has_nodes:
        covered_free_pixels += region_size

overall_coverage = covered_free_pixels / total_free_pixels
```

#### Average Distance to Node（ノードまでの平均距離）

**理想値**: できるだけ小さく（マップ解像度の5-10倍程度）

**意味**: 任意の点からノードまでの平均距離

**判断基準**:
- ✅ **低い値**: ロボットが素早くグラフに接続できる
- ❌ **高い値**: グラフが疎すぎ、経路探索の精度が低下

**トレードオフ**: 距離を小さくするにはノード数を増やす必要があり、計算コストが増加

#### Coverage Efficiency（カバレッジ効率）

**理想値**: 高いほど良い（ただし絶対値は環境依存）

**計算式**: `カバレッジ ÷ ノード数`

**意味**: 少ないノードで広範囲をカバーできているか

### 2. グラフ構造指標（Graph Structure Metrics）

実装: `calculate_graph_metrics()` (graph_evaluator.py:162)

#### Number of Nodes & Edges

**理想値**: 用途による
- 小型環境: 50-200ノード
- 中型倉庫: 200-1000ノード
- 大型施設: 1000+ノード

**重要な比率**: `エッジ数 ÷ ノード数 ≈ 2.5-4.0`
- 平面グラフの理論値: 最大3倍（Euler's formula）
- Delaunay三角分割: 約3倍
- 実用的なグラフ: 2.5-4倍（適度な接続性）

#### Average Node Degree（平均次数）

**理想値**: 3-5

**意味**: 各ノードの平均接続数

**判断基準**:
- ✅ **3-5**: 最適 - 複数の経路選択肢があり効率的
- ⚠️ **2-3**: やや疎 - 代替経路が少ない
- ⚠️ **6+**: やや密 - 冗長な接続が多い
- ❌ **2未満**: 線形グラフに近く、柔軟性が低い

```python
average_degree = np.mean([d for _, d in self._graph.degree()])
```

#### Average Edge Length

**理想値**: マップサイズの5-10%程度

**判断基準**:
- ✅ **適度な長さ**: 効率的なカバレッジ
- ❌ **長すぎ**: グラフが疎すぎ、経路が不正確
- ❌ **短すぎ**: ノードが密集しすぎ、計算コスト増

#### Graph Diameter（グラフ直径）

**理想値**: できるだけ小さく

**意味**: 最も遠い2ノード間の最短経路長

**判断基準**:
- ✅ **小さい**: どこへでも素早く到達可能
- ❌ **大きい**: 遠距離移動に時間がかかる
- ❌ **inf（無限大）**: グラフが非連結（重大な問題）

### 3. 経路計画指標（Path Planning Metrics）

実装: `calculate_path_metrics()` (graph_evaluator.py:205)

#### Path Success Rate（経路成功率）

**理想値**: 100%（連結グラフの場合）

**意味**: ランダムなノードペア間で経路が見つかる割合

**判断基準**:
- ✅ **100%**: 完全連結 - どこへでも行ける
- ⚠️ **95-99%**: ほぼ連結 - 一部孤立ノードあり
- ❌ **95%未満**: 非連結 - 多数のサブグラフに分断

```python
for _ in range(num_samples):
    start, end = random.sample(nodes, 2)
    try:
        path = nx.shortest_path(self._graph, start, end, weight="weight")
        num_paths += 1
    except nx.NetworkXNoPath:
        continue

path_success_rate = num_paths / num_samples
```

#### Average Path Length（平均経路長）

**理想値**: 直線距離の1.1-1.5倍

**意味**: 経路の平均長さ

**判断基準**:
- ✅ **直線距離に近い**: 効率的な経路
- ⚠️ **1.5-2.0倍**: やや迂回あり
- ❌ **2.0倍以上**: 大きく迂回、グラフ構造に問題

#### Average Path Smoothness（経路の滑らかさ）

**理想値**: 0.7以上

**スケール**: 0（急な曲がり多数）～ 1（完全に滑らか）

**判断基準**:
- ✅ **0.8-1.0**: 非常に滑らか - ロボット移動に最適
- ⚠️ **0.6-0.8**: 許容範囲 - 一部急カーブあり
- ❌ **0.6未満**: ギザギザな経路 - 動作効率低下

**計算方法** (graph_evaluator.py:333):
```python
def _calculate_path_smoothness(self, path):
    angles = []
    for i in range(len(path) - 2):
        p1 = np.array(path[i])
        p2 = np.array(path[i + 1])
        p3 = np.array(path[i + 2])

        v1 = p2 - p1
        v2 = p3 - p2

        # ベクトル間の角度を計算
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle = np.arccos(cos_angle)
        angles.append(angle)

    # 滑らかさ指標に変換（1 = 滑らか, 0 = 急カーブ）
    smoothness = 1.0 - np.mean(angles) / np.pi
    return smoothness
```

#### Average Path Clearance（経路クリアランス）

**理想値**: 安全距離の1.5倍以上

**意味**: 経路上の障害物までの平均距離

**判断基準**:
- ✅ **高い値**: 安全マージン大、衝突リスク低
- ⚠️ **安全距離程度**: 最低限の安全性
- ❌ **安全距離未満**: 衝突リスク高（検証エラー）

**計算方法** (graph_evaluator.py:357):
```python
def _calculate_path_clearance(self, path):
    clearances = []
    for i in range(len(path) - 1):
        # Bresenhamアルゴリズムで経路上の全ピクセルを取得
        line_points = bresenham_line(start[0], start[1], end[0], end[1])
        for y, x in line_points:
            # 事前計算された距離マップから障害物までの距離を取得
            clearance = self._distance_map[y, x]
            clearances.append(clearance)

    return np.mean(clearances)
```

### 4. 検証指標（Validation Metrics）

実装: `calculate_validation_metrics()` (graph_evaluator.py:275)

これらは**必須条件**で、どれか1つでも失敗すると**グラフは使用不可**です。

#### Collision Free（衝突なし）

**必須**: True

**意味**: 全エッジが障害物と交差していないか

**判断**: Falseなら**致命的エラー**

**検証方法** (graph_evaluator.py:320):
```python
def _check_all_edges_collision(self):
    edge_image = self._inflated_map.copy()

    # 全エッジを画像上に描画
    for n1, n2 in self._graph.edges():
        pixel1 = self._graph.nodes[n1]["pixel"]
        pixel2 = self._graph.nodes[n2]["pixel"]
        cv2.line(edge_image, pixel1[::-1], pixel2[::-1], color=0, thickness=1)

    # 変化がなければ衝突なし
    return np.all(edge_image == self._inflated_map)
```

#### Node Validity（ノード妥当性）

**必須**: True

**意味**: 全ノードが自由空間内にあるか

**判断**: Falseなら**設定エラー**（安全距離が不適切）

#### Connectivity（連結性）

**理想**: True（完全連結）

**意味**: グラフが1つの連結成分か

**判断**:
- True: どのノードからも全ノードへ到達可能
- False: 複数のサブグラフに分断（用途によっては許容）

#### Number of Subgraphs（サブグラフ数）

**理想値**: 1

**判断**:
- 1: 完全連結
- 2-3: 環境が物理的に分離（例: 複数フロア） - 許容可
- 4+: 問題あり - パラメータ調整が必要

### 実践的な判断基準

#### 🏆 優秀なグラフの例

```
Coverage Metrics:
  - Free Space Coverage: 98.5%          ✅
  - Average Distance to Node: 3.2 pixels ✅
  - Coverage Efficiency: 0.0045         ✅

Graph Structure:
  - Number of Nodes: 450               ✅
  - Number of Edges: 1580              ✅ (3.5倍)
  - Average Node Degree: 3.8           ✅

Path Planning:
  - Path Success Rate: 100%            ✅
  - Average Path Smoothness: 0.82      ✅
  - Average Path Clearance: 8.5 pixels ✅

Validation:
  - Collision Free: True               ✅
  - Graph Connected: True              ✅
  - Number of Subgraphs: 1             ✅
```

#### ⚠️ 改善が必要なグラフの例

```
Coverage Metrics:
  - Free Space Coverage: 65%           ❌ 疎すぎ
  - Average Distance to Node: 15 pixels ❌ 遠すぎ

Graph Structure:
  - Average Node Degree: 1.8           ❌ 線形的

Path Planning:
  - Path Success Rate: 87%             ❌ 非連結
  - Average Path Smoothness: 0.45      ❌ ギザギザ

Validation:
  - Number of Subgraphs: 5             ❌ 分断
```

**改善方法**:
- `free_space_sampling_threshold`を小さくしてノード密度を上げる
- `skeleton_sample_distance`を小さくする
- `use_delaunay_shortcuts=True`でショートカット追加

### グラフ評価のトレードオフ

グラフの「良さ」は**バランス**です：

| トレードオフ | 詳細 |
|------------|------|
| **カバレッジ vs ノード数** | カバレッジを上げるとノード数増加 → 計算コスト増 |
| **経路精度 vs グラフ密度** | 精度を上げるとグラフが密に → メモリ使用量増 |
| **滑らかさ vs 経路長** | 滑らかな経路は迂回する可能性 → 移動時間増 |
| **安全性 vs 効率** | 安全マージンを増やすと経路選択肢減 → 迂回増 |

**用途別の優先順位**:

- **倉庫ロボット**: カバレッジ > 経路長 > 滑らかさ
- **自動運転車**: 安全性 > 滑らかさ > 経路長
- **ドローン**: 経路長 > カバレッジ > 滑らかさ

---

## Git LFSについて

### Git LFSとは

**Git LFS (Large File Storage)** は、大きなバイナリファイルをGitリポジトリで効率的に管理するための拡張機能です。

### 仕組み

通常のGitでは、大きなファイル（画像、動画、モデルファイルなど）をコミットすると:
- リポジトリサイズが肥大化
- クローンやプルが遅くなる
- 履歴に全バージョンが保存されるため容量が増え続ける

Git LFSを使うと:
1. **ポインタファイル**（小さなテキストファイル）だけをGitで管理
2. **実際のファイル**は別のLFSサーバーに保存
3. 必要なときだけ実ファイルをダウンロード

### このリポジトリでの使用状況

`.gitattributes`で以下のファイルタイプがLFS管理されています:

```
画像: *.gif, *.jpg, *.png, *.psd
アーカイブ: *.gz, *.tar, *.zip
ドキュメント: *.pdf
共有ライブラリ: *.so
```

具体的には:
- **マップファイル** (`maps/carter_warehouse_navigation.png` など)
- **ドキュメント画像** (`docs/images/` 内の画像)
- **デモGIF** (`generation_in_action.gif`)

### ポインタファイルの例

```bash
$ cat maps/carter_warehouse_navigation.png
version https://git-lfs.github.com/spec/v1
oid sha256:dd2f5e382a5f331866becaeaffb391a7e46b595873bf25c9cbb4e280ec261b8e
size 4563  # 実際のファイルは4.5KB
```

このファイルは現在**ポインタファイル（129バイト）**だけで、実際の画像（4.5KB）はまだダウンロードされていません。

### コマンドの使い方

```bash
# リポジトリをクローン（ポインタファイルのみ）
git clone <repo>

# 実際のファイルをダウンロード
git lfs pull
```

### 必要性の判断

✅ **Git LFS pullが必要なケース:**
- マップファイル（PNG画像）を使ってグラフを生成したい
- サンプルスクリプト（`scripts/generate_graph.py`など）を実行したい
- ドキュメントの画像を閲覧したい

❌ **Git LFS pullが不要なケース:**
- コードを読むだけ
- 自分のマップファイルを使う予定
- ライブラリとしてインストールするだけ

### Git LFSのインストール

```bash
# Ubuntu/Debian
sudo apt-get install git-lfs
git lfs install

# macOS
brew install git-lfs
git lfs install
```

---

## CPU版について

**このフォーク（nkys39/swagger）**は**CPU環境で動作**します。CUDA/GPUは不要です。

> **重要**: CPU専用版は**このフォークのみ**の機能です。オリジナルのNVIDIA公式リポジトリ（nvidia-isaac/SWAGGER）にはCUDA依存があります。

### フォークでの変更内容

以下の変更により、CUDA依存を完全に削除しました:

1. **pyproject.toml**: `cucim-cu12`パッケージを削除
2. **waypoint_graph_generator.py**:
   - `cupy`と`cucim`のimportを削除
   - `skimage.morphology.skeletonize`（CPU版）を使用
3. **README.md**: システム要件からCUDA記載を削除

コミット: `1314408 - Remove CUDA dependencies to enable CPU-only execution`

### パフォーマンスへの影響

**変更箇所**: スケルトン生成処理のみ

- **GPU版（cucim）**: CUDA高速化あり - オリジナル版で使用
- **CPU版（skimage）**: やや遅いが機能的には同等 - **このフォークで使用**

**他の処理**: 元々CPUで実行されていたため影響なし
- 距離変換（OpenCV）
- Delaunay三角分割（Scipy）
- グラフ操作（NetworkX）

### インストール（CPU専用版）

#### uvを使う方法（推奨）

```bash
# CUDA不要！このフォークを使用
git clone git@github.com:nkys39/swagger.git
cd swagger

# オプション: サンプルマップを使う場合のみ
git lfs pull

# 依存パッケージのインストール
sudo apt update && sudo apt install -y libgl1-mesa-glx libglib2.0-0

# uvで仮想環境を作成してインストール
uv venv
source .venv/bin/activate
uv pip install -e .
```

#### pip/venvを使う方法（従来）

```bash
# CUDA不要！このフォークを使用
git clone git@github.com:nkys39/swagger.git
cd swagger

# オプション: サンプルマップを使う場合のみ
git lfs pull

# 依存パッケージのインストール
sudo apt update && sudo apt install -y libgl1-mesa-glx libglib2.0-0

# 仮想環境の作成とライブラリインストール
python -m venv swagger-venv
source swagger-venv/bin/activate
pip install -e .
```

従来のCUDA要件（CUDA 12.5、NVIDIA CUDA toolkit）は**不要**です。

### ベンチマーク参考

CPU版とGPU版の処理時間比較（参考値）:

| マップサイズ | CPU版（skimage） | GPU版（cucim） |
|------------|----------------|---------------|
| 500×500    | 0.5秒          | 0.1秒         |
| 1000×1000  | 2.0秒          | 0.3秒         |
| 2000×2000  | 8.0秒          | 1.0秒         |

※ スケルトン生成のみの時間。環境により異なります。

---

## 参考リンク

### リポジトリ

- [オリジナル公式リポジトリ（GPU版）](https://github.com/nvidia-isaac/SWAGGER)
- [このフォーク（CPU専用版）](https://github.com/nkys39/swagger)

### ドキュメント

- [アルゴリズム概要](docs/algorithm.md)
- [チュートリアル](docs/tutorial.md)
- [評価方法](docs/evaluation.md)
- [統合例](integration/README.md)

---

## ライセンス

Apache License 2.0

## 著者

Rushane Hua, Billy Okal, Benjamin Butin

## 貢献

貢献を歓迎します！詳細は [CONTRIBUTING.md](CONTRIBUTING.md) をご覧ください。
