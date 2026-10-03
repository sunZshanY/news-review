# -*- coding: utf-8 -*-
"""build_package.py — 打包今日新闻插件为 .cwplugin / .zip（与 CI 的 cw-plugin-pack 布局一致）"""

import os
import shutil
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))

# 包内文件（相对路径）
FILES = [
    "main.py",
    "news_sources.py",
    "cwplugin.json",
    "icon.png",
    "README.md",
    "qml/news_widget.qml",
    "qml/settings.qml",
    "qml/widget_settings.qml",
]

VERSION = "1.6.3+1"


def build_zip(target: str) -> None:
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in FILES:
            src = os.path.join(ROOT, rel)
            if not os.path.isfile(src):
                raise SystemExit(f"缺少文件: {rel}")
            z.write(src, rel)
    print(f"已生成: {target} ({os.path.getsize(target)} 字节)")


def main():
    # 1. 仓库根目录（发布上传用）
    build_zip(os.path.join(ROOT, "com.newsreview.news.cwplugin"))
    build_zip(os.path.join(ROOT, "com.newsreview.news.zip"))

    # 2. dist 目录
    dist = os.path.join(ROOT, "dist")
    os.makedirs(dist, exist_ok=True)
    build_zip(os.path.join(dist, "com.newsreview.news.cwplugin"))
    build_zip(os.path.join(dist, "com.newsreview.news.zip"))
    build_zip(os.path.join(dist, f"news-review-{VERSION}.cwplugin"))
    build_zip(os.path.join(dist, f"news-review-{VERSION}.zip"))

    # 3. 清理旧版本产物
    for stale in ("news-review-1.5.2.cwplugin", "news-review-1.5.2.zip",
                  "news-review-1.7.0.cwplugin", "news-review-1.7.0.zip"):
        p = os.path.join(dist, stale)
        if os.path.isfile(p):
            os.remove(p)
            print(f"已移除旧产物: {p}")


if __name__ == "__main__":
    main()
