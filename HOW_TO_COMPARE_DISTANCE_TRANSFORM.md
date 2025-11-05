# STEP1 距離変換の比較方法

PythonとC++の距離変換（distance transform）の実装が一致しているか確認する方法です。

## 背景

距離変換はSTEP1で実行され、その結果がSTEP2以降のすべてのステップに影響します。
PythonとC++で結果が異なると、最終的なグラフが一致しません。

## 実装の確認

### Python実装
- **場所**: `scripts/steps/step1_preprocess.py:56`
- **関数**: `cv2.distanceTransform(free_map_padded, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)`
- **パラメータ**:
  - 距離タイプ: `cv2.DIST_L2` (ユークリッド距離)
  - マスクサイズ: `cv2.DIST_MASK_PRECISE` (正確な計算)

### C++実装
- **場所**: `swagger-cpp/src/step1_preprocess.cpp:34`
- **関数**: `cv::distanceTransform(padded, dist_full, cv::DIST_L2, cv::DIST_MASK_PRECISE)`
- **パラメータ**:
  - 距離タイプ: `cv::DIST_L2` (ユークリッド距離)
  - マスクサイズ: `cv::DIST_MASK_PRECISE` (正確な計算)

## 比較手順

### 1. Pythonのstep1を実行

```bash
python scripts/steps/step1_preprocess.py \
  --map data/maps/example.pgm \
  --resolution 0.05 \
  --safety-distance 0.5 \
  --output output/python
```

これにより以下のファイルが生成されます：
- `debug_output/python_step1_dist_transform.npy` - 距離変換マップ（float32）
- `debug_output/python_step1_inflated_map.png` - 膨張マップ（uint8）

### 2. C++のstep1を実行

```bash
cd swagger-cpp
mkdir -p build && cd build
cmake ..
make
./swagger_cpp --map ../../data/maps/example.pgm \
  --resolution 0.05 \
  --safety-distance 0.5 \
  --output ../../output/cpp
```

これにより以下のファイルが生成されます：
- `debug_output/cpp_step1_dist_transform.npy` - 距離変換マップ（float32）
- `debug_output/cpp_step1_inflated_map.png` - 膨張マップ（uint8）

### 3. 比較スクリプトを実行

```bash
python compare_distance_transform.py
```

## 比較結果の読み方

### ✅ 理想的な結果（完全一致）

```
Distance maps identical (tolerance=1e-6): True
Inflated maps identical: True
✅ RESULT: Distance transforms are IDENTICAL
```

### ⚠️ 問題がある場合

```
Distance maps identical (tolerance=1e-6): False
  Maximum difference: 0.000123456
  Mean difference: 0.000001234
  Pixels with diff > 1e-6: 1234 / 1000000 (0.12%)

Inflated maps identical: False
  Python occupied pixels: 12345
  C++ occupied pixels:    12346
  Difference:             1
  Different pixels: 1 / 1000000 (0.00%)
```

## 問題の原因候補

距離変換が一致しない場合、以下の原因が考えられます：

### 1. **データ型の違い**
- Python: `float32` (デフォルト)
- C++: OpenCVのデフォルトは`CV_32F`だが、明示的に指定されているか？

### 2. **入力データの違い**
- パディングの方法
- 自由空間マップの生成方法（occupancy_thresholdの適用）

### 3. **OpenCVのバージョン違い**
- 距離変換の内部実装がバージョンで異なる可能性

### 4. **浮動小数点の丸め誤差**
- 完全一致ではないが、許容範囲内（< 1e-6）なら問題なし

### 5. **コンパイラ最適化の影響**
- `-O3`などの最適化フラグによる浮動小数点演算の違い

## 次のステップ

### 完全に一致する場合
距離変換は正しく実装されています。問題は他のステップ（STEP2のスケルトン生成など）にあります。

### 一致しない場合
1. `dist_transform`と`inflated_map`のどちらが異なるか確認
2. `inflated_map`が異なる場合は、閾値判定の実装を確認
3. `dist_transform`自体が異なる場合は、入力データ（free_map）を確認

## トラブルシューティング

### ファイルが見つからない

```bash
# debug_outputディレクトリを確認
ls -la debug_output/

# 必要に応じて手動で作成
mkdir -p debug_output
```

### コンパイルエラー

```bash
# C++の依存関係を確認
cd swagger-cpp/build
cmake .. && make VERBOSE=1
```

### 比較スクリプトのエラー

```bash
# Pythonの依存関係をインストール
pip install numpy opencv-python
```

## 参考

- OpenCV distance transform ドキュメント: https://docs.opencv.org/4.x/d7/d1b/group__imgproc__misc.html#ga8a0b7fdfcb7a13dde018988ba3a43042
- cv2.DIST_L2: ユークリッド距離
- cv2.DIST_MASK_PRECISE: 5x5マスクによる正確な計算
