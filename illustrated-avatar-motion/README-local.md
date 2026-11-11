# 本地流程

所有命令在本 SKILL.md 所在目录运行。
Python 3.10+。依赖安装：python -m pip install -r requirements.txt

## 新人物
先读取 SKILL.md。创建独立 cases/<slug>，保留原始 source 文件，先完成裁切、等比例补方和必要的风格生成。
以下命令替换尖括号占位：

    python matte.py <prepared-square-image> --out cases/<slug>/canonical.png --json
    python extract-eyes.py cases/<slug>/canonical.png --out cases/<slug>/eyes.json --json
    python build-pack.py cases/<slug>/canonical.png --eyes cases/<slug>/eyes.json --out cases/<slug> --id <slug> --json

必要时人工校准两眼，数值为当前 canonical 的实测像素：

    python extract-eyes.py cases/<slug>/canonical.png --correct left=<cx,cy,w,h> --correct right=<cx,cy,w,h> --out cases/<slug>/eyes.json --json

canonical 可为 1024 方图，构建结果为 744px。不要将 canonical 的像素眼框直接用于 744px front.png。

## 去眼检查
inspect-eyeless.py 读取 layers/canonical-eyeless.png 和 layers/eyes.json。
在 canonical 原尺度调用 packlib.make_eyeless 生成前者，将本人物 eyes.json 复制为后者。
不能把尺寸不同的 front.png 简单重命名成 canonical-eyeless.png。

    python inspect-eyeless.py cases/<slug>/evidence cases <slug>

此命令只有位置参数，没有 --json；旧版 --help 不可用。结果须有该人物，不能接受空 cases。

## 预览与导出

    python serve.py
    python export-pack.py <slug> --out exports/<slug>.zip

先将 templates/preview.html 和 templates/preview.js 复制到 cases/<slug>/。
预览 http://127.0.0.1:8766/cases/<slug>/preview.html。若端口被无关服务占用，在当前 PowerShell 设置 $env:ILLUSTRATED_AVATAR_PORT 后启动。
导出 ZIP 解压后运行 python serve.py。包中只带当前人物和必需工具、demo、runtime，许可信息随附。
图片构建需要 Pillow/numpy，静态播放不要求它们。

## 已知边界
照片转插画依赖宿主生成工具。自动检测眼睛、外缘颜色需要视觉复核。
原包独立运行时与旧灰发/粉发页面不同，逐图验收后再交付。
