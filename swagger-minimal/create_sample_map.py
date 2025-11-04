#!/usr/bin/env python3
"""サンプル占有グリッドマップを作成するスクリプト"""

import cv2
import numpy as np
import os


def create_sample_map():
    """テスト用のサンプルマップを作成する"""

    # 空白マップを作成（500x500、すべて白=自由空間）
    map_img = np.ones((500, 500), dtype=np.uint8) * 255

    # 矩形の障害物を追加（黒=占有）
    cv2.rectangle(map_img, (100, 100), (400, 150), 0, -1)
    cv2.rectangle(map_img, (100, 200), (150, 400), 0, -1)
    cv2.rectangle(map_img, (300, 250), (400, 400), 0, -1)

    # 円形の障害物を追加
    cv2.circle(map_img, (250, 350), 50, 0, -1)

    # 保存
    os.makedirs('maps', exist_ok=True)
    output_path = 'maps/sample_map.png'
    cv2.imwrite(output_path, map_img)
    print(f"サンプルマップを作成しました: {output_path}")
    print(f"マップサイズ: {map_img.shape}")
    print(f"自由空間（白）: 255")
    print(f"占有空間（黒）: 0")


if __name__ == "__main__":
    create_sample_map()
