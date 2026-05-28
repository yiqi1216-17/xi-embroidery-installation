# Xi Embroidery P-D-P Installation

**绣纹流光·粒影生花** — 锡绣非遗 AI+AR 互动装置的 **感知层与本地显示层** 代码。

对应 P-D-P 范式中的 **Physical → Digital** 链路：用户举起纹样卡片 → 摄像头识别 → 驱动 TouchDesigner / 本地画布显示。

## 系统架构

```
用户卡片 → 摄像头
              ↓
     perception/   SIFT + FLANN 匹配（13 纹样）
              ↓
     orchestrator/ 多帧投票 + 序列轮播
              ↓
     drivers/       写入 current_video_path.txt
              ↓
     display/       本地 OpenCV 预览（或 TouchDesigner 读取）
```

完整装置还包含（不在本仓库）：
- **渲染层**：TouchDesigner 粒子系统
- **生成层**：Stable Diffusion + LoRA
- **体验层**：Kivicube WebAR

## 目录结构

```
├── assets/manifest.json    # 13 纹样元数据（坐标、参考图）
├── config/
│   ├── accurate.yaml       # 展览精度模式
│   └── fast.yaml           # 本地流畅模式
├── src/xi_embroidery/      # 核心包
├── scripts/                # 启动脚本
├── tests/
└── requirements.txt
```

## 安装

```bash
cd TD_project
python3 -m pip install -r requirements.txt
```

需要 OpenCV SIFT（`opencv-contrib-python` 已包含在 requirements 中）。

## 运行

```bash
# 一键：识别 + 显示（展览精度）
python3 scripts/run_local.py --mode accurate

# 本地流畅预览
python3 scripts/run_local.py --mode fast

# 仅识别端 / 仅显示端
python3 scripts/run_perception.py --mode accurate
python3 scripts/run_display.py --mode accurate
```

按 `q` 退出各窗口。

## 配置说明

| 参数 | accurate | fast |
|------|----------|------|
| 参考图缩放 | 不缩小 | 600px |
| 摄像头帧缩放 | 原尺寸 | 35% |
| SIFT 特征点 | 不限制 | 250 |
| 识别间隔 | 0.5s | 0.8s |
| 多帧投票 | 3 次 | 2 次 |

编辑 `config/accurate.yaml` 或 `config/fast.yaml` 即可调参，无需改代码。

## 与 TouchDesigner 对接

识别结果写入项目根目录 `current_video_path.txt`：

```
video10,-0.03,-0.14,/path/to/assets/video10-1.png
```

TouchDesigner 定时读取该文件，按坐标叠加对应序列帧。

## 测试

```bash
python3 -m unittest discover -s tests -v
```

## 日志

识别事件写入 `logs/events.jsonl`（用于体验分析，已加入 `.gitignore`）。

