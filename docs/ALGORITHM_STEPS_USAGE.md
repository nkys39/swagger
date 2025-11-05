# アルゴリズムステップの個別制御

このドキュメントでは、SWAGGERの各アルゴリズムステップを個別にオン/オフして実行する方法を説明します。

## 概要

SWAGGERのグラフ生成は以下の6つのステップで構成されています：

1. **安全バッファの追加** (常に実行)
2. **スケルトングラフの構築** (`--use-skeleton-graph`)
3. **境界ノードの作成** (`--use-boundary-sampling`)
4. **自由空間のノード配置** (`--use-free-space-sampling`)
5. **三角分割とエッジ追加** (`--use-delaunay-shortcuts`)
6. **グラフの剪定** (`--prune-graph`)

## 基本的な使い方

### すべてのステップを有効化（デフォルト）

```bash
python scripts/generate_graph.py \
    --map-path maps/your_map.png
```

### 特定のステップのみを実行

各ステップは `--no-` プレフィックスで無効化できます：

```bash
# スケルトングラフのみを無効化
python scripts/generate_graph.py \
    --map-path maps/your_map.png \
    --no-use-skeleton-graph
```

## 実用例

### 例1: スケルトングラフのみ（ステップ2のみ）

最も基本的なグラフ（medial axis）のみを生成します。

```bash
python scripts/generate_graph.py \
    --map-path maps/your_map.png \
    --use-skeleton-graph \
    --no-use-boundary-sampling \
    --no-use-free-space-sampling \
    --no-use-delaunay-shortcuts \
    --no-prune-graph \
    --output-dir output/skeleton_only
```

**特徴:**
- 最もシンプルなグラフ
- ノード数が少ない
- 障害物から最も遠い経路を提供

**用途:**
- 基本的な経路計画
- 計算リソースが限られている場合

---

### 例2: スケルトン + 境界サンプリング（ステップ2+3）

障害物付近のカバレッジを改善します。

```bash
python scripts/generate_graph.py \
    --map-path maps/your_map.png \
    --use-skeleton-graph \
    --use-boundary-sampling \
    --no-use-free-space-sampling \
    --no-use-delaunay-shortcuts \
    --no-prune-graph \
    --output-dir output/skeleton_and_boundary
```

**特徴:**
- 障害物に沿った経路が利用可能
- 狭い通路でのカバレッジ向上

**用途:**
- 壁に沿った移動が必要な場合
- 狭い環境でのナビゲーション

---

### 例3: 自由空間サンプリングのみ（ステップ4のみ）

広い空間を均等にカバーします。

```bash
python scripts/generate_graph.py \
    --map-path maps/your_map.png \
    --no-use-skeleton-graph \
    --no-use-boundary-sampling \
    --use-free-space-sampling \
    --no-use-delaunay-shortcuts \
    --no-prune-graph \
    --output-dir output/free_space_only
```

**特徴:**
- 広い空間での均等なノード配置
- 局所最大値ベースの配置

**用途:**
- 広い倉庫や駐車場
- 均等なカバレッジが必要な場合

---

### 例4: 剪定なし（ステップ6を無効化）

すべてのノードとエッジを保持します。

```bash
python scripts/generate_graph.py \
    --map-path maps/your_map.png \
    --no-prune-graph \
    --output-dir output/no_pruning
```

**特徴:**
- 冗長なノードも保持
- より密なグラフ

**用途:**
- デバッグ
- 最大カバレッジが必要な場合

---

### 例5: Delaunayショートカットなし（ステップ5を無効化）

直接的なショートカットを追加しません。

```bash
python scripts/generate_graph.py \
    --map-path maps/your_map.png \
    --no-use-delaunay-shortcuts \
    --output-dir output/no_shortcuts
```

**特徴:**
- より少ないエッジ
- 経路が長くなる可能性

**用途:**
- エッジ数を削減したい場合
- メモリ制約がある場合

---

## パラメータの調整

各ステップのパラメータもコマンドラインから調整できます：

```bash
python scripts/generate_graph.py \
    --map-path maps/your_map.png \
    --skeleton-sample-distance 2.0 \
    --boundary-sample-distance 3.0 \
    --free-space-sampling-threshold 2.0 \
    --merge-node-distance 0.5 \
    --min-subgraph-length 0.5
```

### パラメータ一覧

| パラメータ | デフォルト | 説明 |
|-----------|----------|------|
| `--skeleton-sample-distance` | 1.5m | スケルトンサンプリング間隔 |
| `--boundary-inflation-factor` | 1.5 | 境界膨張率（無次元） |
| `--boundary-sample-distance` | 2.5m | 境界サンプリング間隔 |
| `--free-space-sampling-threshold` | 1.5m | 自由空間サンプリング閾値 |
| `--merge-node-distance` | 0.25m | ノードマージ距離 |
| `--min-subgraph-length` | 0.25m | 最小サブグラフ長 |

## 実験とデバッグ

### ステップごとの比較

各ステップの効果を視覚的に比較：

```bash
# ステップ2のみ
python scripts/generate_graph.py \
    --use-skeleton-graph \
    --no-use-boundary-sampling \
    --no-use-free-space-sampling \
    --no-use-delaunay-shortcuts \
    --no-prune-graph \
    --output-dir step2_only

# ステップ2+3
python scripts/generate_graph.py \
    --use-skeleton-graph \
    --use-boundary-sampling \
    --no-use-free-space-sampling \
    --no-use-delaunay-shortcuts \
    --no-prune-graph \
    --output-dir step2_3

# ステップ2+3+4
python scripts/generate_graph.py \
    --use-skeleton-graph \
    --use-boundary-sampling \
    --use-free-space-sampling \
    --no-use-delaunay-shortcuts \
    --no-prune-graph \
    --output-dir step2_3_4

# すべてのステップ
python scripts/generate_graph.py \
    --output-dir step_all
```

### グラフ統計の比較

```bash
# ノード数とエッジ数を比較
for dir in step2_only step2_3 step2_3_4 step_all; do
    echo "=== $dir ==="
    grep -E "nodes|edges" $dir/graph.gml | head -2
done
```

## ヘルプの表示

すべてのオプションを確認：

```bash
python scripts/generate_graph.py --help
```

## よくある質問

### Q: どのステップの組み合わせが最適ですか？

**A:** 環境によります：

- **倉庫**: すべてのステップを有効化（デフォルト）
- **狭い廊下**: スケルトン + 境界サンプリング
- **広い空間**: 自由空間サンプリング + Delaunay
- **計算制約**: スケルトンのみ

### Q: ステップを無効化すると何が起こりますか？

**A:**
- ノード数が減少
- カバレッジが低下する可能性
- 処理速度が向上
- メモリ使用量が削減

### Q: パラメータを大きくするとどうなりますか？

**A:**
- サンプリング間隔を**大きく**すると → ノード数**減少**
- サンプリング閾値を**大きく**すると → ノード数**減少**
- マージ距離を**大きく**すると → ノード数**減少**

## トラブルシューティング

### グラフが空になる

すべてのステップを無効化すると、グラフが生成されません：

```bash
# これは動作しません
python scripts/generate_graph.py \
    --no-use-skeleton-graph \
    --no-use-boundary-sampling \
    --no-use-free-space-sampling
```

少なくとも1つのステップ（2, 3, 4のいずれか）を有効化してください。

### ノードが多すぎる

パラメータを調整してノード数を削減：

```bash
python scripts/generate_graph.py \
    --skeleton-sample-distance 3.0 \
    --boundary-sample-distance 5.0 \
    --free-space-sampling-threshold 3.0
```

または、一部のステップを無効化：

```bash
python scripts/generate_graph.py \
    --no-use-free-space-sampling
```

## 参考リンク

- [アルゴリズム詳細](docs/algorithm.md)
- [日本語ガイド](README_ja.md)
- [チュートリアル](docs/tutorial.md)
