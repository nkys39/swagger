# SWAGGER 日本語ガイド

**SWAGGER (Sparse WAypoint Graph Generation for Efficient Routing)** は、占有グリッドマップから経路計画用のスパースなウェイポイントグラフを自動生成するPythonパッケージです。

> **注意**: このリポジトリはCPU専用版（CUDA依存を削除したフォーク）です。

## クイックスタート

```bash
# 1. リポジトリをクローン
git clone https://github.com/nkys39/swagger.git
cd swagger

# 2. 仮想環境を作成してインストール
uv venv && source .venv/bin/activate
uv pip install -e .

# 3. サンプルマップで実行
python scripts/run_pipeline.py \
  --map data/maps/example.pgm \
  --output output \
  --save-gml

# 4. 結果を確認
ls -lh output/
```

---

## 主な特徴

- 🗺️ **占有グリッドマップから自動生成**: PGM/PNG形式のマップを入力
- 🦴 **スケルトンベース**: Medial axis（中心線）に沿った効率的なグラフ
- 🎯 **障害物境界カバレッジ**: 境界サンプリングで障害物付近もカバー
- 🚀 **Delaunayショートカット**: 三角分割による最短経路エッジ
- 💻 **CPU環境で動作**: CUDA不要（このフォーク）
- 🔧 **C++実装あり**: Python実装との比較・検証用

---

## プロジェクト構成

このリポジトリには複数の実装が含まれています：

| ディレクトリ | 言語 | ステップ | 用途 |
|------------|------|---------|------|
| **swagger/** | Python | 全6ステップ | メイン実装・本番用 |
| **swagger-minimal/** | Python | Step1+3 | 軽量版・学習用 |
| **swagger-cpp/** | C++ | 全6ステップ | Python比較・検証用 |
| **swagger-minimal-cpp/** | C++ | Step1+3 | C++軽量版 |
| **scripts/** | Python | - | パイプライン実行スクリプト |
| **tools/** | Python | - | 比較・可視化ツール |
| **docs/** | - | - | ドキュメント |

### 各プロジェクトの詳細

- **swagger/ (Pythonメイン実装)**: パッケージとして使用可能な完全実装
- **[swagger-minimal/](swagger-minimal/README_ja.md)**: Step1+3のみの軽量版（学習用）
- **[swagger-cpp/](swagger-cpp/README_ja.md)**: Python実装との比較・検証用C++完全実装
- **[swagger-minimal-cpp/](swagger-minimal-cpp/README_ja.md)**: C++軽量版

---

## システム要件

### Python版
- Python 3.10以降
- Linux (Ubuntu 22.04推奨)
- **CUDA不要**（このフォーク）

### C++版
- C++17対応コンパイラ（GCC 7+）
- CMake 3.15以上
- OpenCV 4.0以上

---

## インストール

### uvを使う（推奨）

```bash
# uvをインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# リポジトリをクローン
git clone https://github.com/nkys39/swagger.git
cd swagger

# 仮想環境を作成してインストール
uv venv
source .venv/bin/activate
uv pip install -e .
```

### pipを使う

```bash
git clone https://github.com/nkys39/swagger.git
cd swagger

python -m venv swagger-venv
source swagger-venv/bin/activate
pip install -e .
```

---

## 使い方

### 基本的な使い方

```bash
# デフォルト設定で実行
python scripts/run_pipeline.py \
  --map data/maps/example.pgm \
  --output output

# GML形式で保存
python scripts/run_pipeline.py \
  --map data/maps/example.pgm \
  --output output \
  --save-gml
```

### パラメータのカスタマイズ

```bash
python scripts/run_pipeline.py \
  --map data/maps/example.pgm \
  --output output \
  --resolution 0.05 \
  --safety-distance 0.5 \
  --skeleton-sample-distance 1.5 \
  --boundary-sample-distance 2.5 \
  --free-space-sampling-threshold 1.5 \
  --save-gml
```

### モジュラー実行（ステップごと）

詳細は[docs/MODULAR_USAGE.md](docs/MODULAR_USAGE.md)を参照：

```bash
# Step 1: 前処理
python scripts/steps/step1_preprocess.py --map data/maps/example.pgm --output output

# Step 2: スケルトングラフ
python scripts/steps/step2_skeleton_graph.py --input output --output output

# Step 3: 境界サンプリング
python scripts/steps/step3_boundary_sampling.py --input output --output output

# 以降のステップも同様...
```

---

## 処理ステップ

SWAGGERは6つのステップでグラフを生成します：

1. **Step 1: 前処理** - 距離変換と障害物膨張
2. **Step 2: スケルトングラフ** - Medial axis抽出とノード配置
3. **Step 3: 境界サンプリング** - 障害物境界にノード追加
4. **Step 4: 自由空間サンプリング** - 大きな自由空間にノード追加
5. **Step 5: Delaunayショートカット** - 三角分割によるエッジ追加
6. **Step 6: グラフプルーニング** - ノード統合と最適化

詳細なアルゴリズム解説は[docs/algorithm_details_ja.md](docs/algorithm_details_ja.md)を参照してください。

---

## C++実装との比較

C++実装（[swagger-cpp/](swagger-cpp/README_ja.md)）は、Python実装との動作比較・検証を目的としています。

### 比較方法

```bash
# 1. Python版を実行
python scripts/run_pipeline.py --map data/maps/example.pgm --output output/python

# 2. C++版を実行
cd swagger-cpp/build
./swagger_cpp --map ../../data/maps/example.pgm --output ../../output/cpp

# 3. 比較ツールで検証
cd ../..
python tools/compare_step_by_step.py
```

比較ツールの詳細は[tools/README.md](tools/README.md)を参照してください。

---

## ドキュメント

### 📚 ガイド・チュートリアル

- [algorithm_details_ja.md](docs/algorithm_details_ja.md) - アルゴリズム詳細解説
- [algorithm.md](docs/algorithm.md) - Algorithm overview (English)
- [tutorial.md](docs/tutorial.md) - Tutorial (English)
- [evaluation.md](docs/evaluation.md) - Evaluation methods (English)

### 🔧 使い方・リファレンス

- [MODULAR_USAGE.md](docs/MODULAR_USAGE.md) - ステップごとの実行方法
- [ALGORITHM_STEPS_USAGE.md](docs/ALGORITHM_STEPS_USAGE.md) - 各ステップの詳細な使い方

### 📤 出力形式・統合

- [GML_AND_NAV2_INTEGRATION_ja.md](docs/GML_AND_NAV2_INTEGRATION_ja.md) - GML形式とROS2統合
- [GML_VISUALIZATION_TOOLS_ja.md](docs/GML_VISUALIZATION_TOOLS_ja.md) - グラフ可視化ツール
- [GML_CPP_GUIDE_ja.md](docs/GML_CPP_GUIDE_ja.md) - C++でのGML処理
- [GRAPH_FORMATS_GUIDE_ja.md](docs/GRAPH_FORMATS_GUIDE_ja.md) - グラフ形式比較

### 🐛 デバッグ・比較

- [tools/README.md](tools/README.md) - 比較・可視化ツールの使い方
- [docs/debug/](docs/debug/) - デバッグガイド

---

## リポジトリのバージョン

| バージョン | リポジトリ | CUDA要件 | 特徴 |
|----------|-----------|---------|------|
| **オリジナル版** | [nvidia-isaac/SWAGGER](https://github.com/nvidia-isaac/SWAGGER) | **必須** (CUDA 12.5+) | GPU高速化あり |
| **CPU専用版（このリポジトリ）** | [nkys39/swagger](https://github.com/nkys39/swagger) | **不要** | CPU環境で動作 |

### CPU版について

このフォークでは以下の変更を行っています：

- **CUDA依存を削除**: `cucim` → `scikit-image`
- **CPU最適化**: NumPy、SciPy、OpenCVのみを使用
- **機能は同等**: グラフ生成アルゴリズムは変更なし
- **C++実装追加**: Python実装との比較・検証用

CPU版とGPU版の処理時間比較：

| マップサイズ | CPU版（skimage） | GPU版（cucim） |
|------------|----------------|---------------|
| 500×500    | 0.5秒          | 0.1秒         |
| 1000×1000  | 2.0秒          | 0.3秒         |
| 2000×2000  | 8.0秒          | 1.0秒         |

※ スケルトン生成のみの時間。環境により異なります。

---

## Git LFSについて

サンプルマップは **Git LFS** で管理されています。

### Git LFSのセットアップ

```bash
# Git LFSをインストール（Ubuntuの場合）
sudo apt-get install git-lfs

# 初期化
git lfs install

# LFSファイルを取得
git lfs pull
```

Git LFSなしでクローンした場合、`data/maps/`のファイルは小さなポインタファイルになります。

---

## ライセンス

Apache License 2.0

## 著者

Rushane Hua, Billy Okal, Benjamin Butin (NVIDIA)

## 貢献

コントリビューションを歓迎します！詳細は[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。

---

## 参考リンク

- [オリジナル公式リポジトリ（GPU版）](https://github.com/nvidia-isaac/SWAGGER)
- [統合例](integration/README.md)
- [サンプルコード](examples/)
