# Xi Embroidery P-D-P Installation

**绣纹流光·粒影生花** — 锡绣非遗 AI+AR 互动装置的 **Python 感知层 + 本地显示层**。

## 项目结构

```
TD_project/
├── assets/
│   ├── manifest.json       # 纹样元数据
│   ├── preview/            # dev 模式轻量资源（脚本生成）
│   ├── audio/              # 装置背景音乐（TouchDesigner 引用）
│   └── image*.png, video*   # 识别参考图与序列帧
├── config/
│   ├── exhibition.yaml     # 展览模式
│   ├── dev.yaml            # 本地开发模式
│   └── overlay_calibration.yaml
├── src/
│   ├── paths.py            # 路径常量
│   ├── settings.py         # 配置加载
│   ├── manifest.py         # 纹样清单
│   ├── perception/         # SIFT 识别
│   ├── orchestrator/       # 状态机 + 日志
│   ├── drivers/            # file / http / websocket 输出
│   └── display/            # 本地 OpenCV 预览
├── scripts/                # 启动与工具脚本
├── tests/
└── TD程序/                 # TouchDesigner 工程（渲染层，非 Python）
```

## 安装与运行

```bash
python3 -m pip install -r requirements.txt

# 展览模式
python3 scripts/run_local.py --mode exhibition

# 本地开发（先生成 preview）
python3 scripts/generate_preview_assets.py
python3 scripts/run_local.py --mode dev
```

## 配置模式

| 模式 | 用途 |
|------|------|
| `exhibition` | 展览部署，全精度 SIFT |
| `dev` | 本地开发，降采样 + preview 资源 |

## 脚本

| 命令 | 说明 |
|------|------|
| `run_perception.py` | 仅识别端 |
| `run_display.py` | 仅显示端 |
| `test_offline_recognition.py` | 离线识别测试 |
| `calibrate_overlay.py` | 纹样位置标定 |
| `generate_preview_assets.py` | 生成 preview 资源 |
| `http_bridge_server.py` | HTTP → txt 桥接 |

## 仓库边界

| 在本仓库 | 不在本仓库 |
|---------|-----------|
| `src/` Python 感知 + 显示 | TouchDesigner 粒子（`TD程序/`） |
| `assets/` 纹样与音频 | Stable Diffusion + LoRA |
| 文件/HTTP 输出驱动 | Kivicube WebAR |

## 大资源说明

- `assets/video*-*.png`、`底图视频4K.mp4` 体积大，建议 Git LFS（见 `.gitattributes`）
- 本地开发用 `assets/preview/`，不依赖原图

## 测试

```bash
python3 -m unittest discover -s tests -v
python3 scripts/test_offline_recognition.py --mode exhibition
```

## 添加多张参考图（手机/侧拍）

编辑 `assets/manifest.json`，为某纹样增加 `references` 数组：

```json
"references": ["image7.png", "image7-phone.png", "image7-angle.png"]
```

把额外参考图放进 `assets/` 即可；识别时会取多张参考图中匹配比最高的一次。

## HTTP 驱动用法

1. 终端 A：`python3 scripts/http_bridge_server.py`
2. 在 `config/exhibition.yaml` 中设置：

```yaml
output:
  driver: http
```

3. 终端 B：`python3 scripts/run_perception.py --mode exhibition`

桥接服务会把 POST 结果写入 `current_video_path.txt`，TouchDesigner 仍可轮询该文件。

