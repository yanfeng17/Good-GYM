# Good-GYM: AI健身助手 💪

<div align="center">

![Good-GYM Logo](assets/Logo-ch.png)

**基于 MediaPipe 姿态检测的智能健身助手 | Docker 一键部署 | 支持 RTSP 摄像头**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-支持-blue.svg)](https://www.docker.com/)

[English](README.md) | [中文](README_CN.md)

</div>

---

## 📖 项目简介

Good-GYM 是一款基于 AI 姿态检测技术的智能健身助手，通过摄像头实时追踪您的运动姿态，自动计数并提供语音反馈。项目采用 Google MediaPipe 进行姿态检测，支持 Docker 容器化部署，可通过 Web 界面远程访问。

### 🎯 核心特性

- **🤖 AI 姿态检测** - 采用 MediaPipe Pose Landmarker 实现精准的 33 关键点追踪
- **🎬 多源视频支持** - 支持本地摄像头、RTSP 网络摄像头、本地视频文件
- **🐳 Docker 部署** - 一键启动，支持打包成 FPK 部署到 FNOS/Docker 环境
- **🌐 Web 界面访问** - 通过浏览器远程访问，支持桌面端和移动端
- **🔊 智能语音播报** - TTS 语音播报次数，里程碑音效（每 10 次）
- **💾 设置持久化** - 运动类型、摄像头地址等配置自动保存
- **📊 运动统计** - 实时追踪健身进度和历史记录
- **🎨 可视化骨骼** - 实时显示人体骨骼和关键角度

## 🆕 最新更新

### v2.0.0 (2026-01-12)
- ✨ 完整 Docker 化支持，支持 RTSP 网络摄像头
- ✨ 新增 WebSocket 音频流，TTS 语音播报
- ✨ FPK 打包支持，可部署到飞牛 OS (FNOS)
- ✨ 设置持久化，容器重启后保留配置
- ✨ 里程碑音效，每 10 次播放特殊音效
- ✨ Web 音频自动连接，移动端音频支持增强
- 🔧 修复重复播报问题
- 🔧 优化音频文件加载（相对路径）

### v1.5.0 (2026-01-09)
- ✨ 迁移到 MediaPipe 姿态检测
- ✨ 解决 ONNX Runtime DLL 依赖问题
- ✨ 提升跨平台兼容性和稳定性

## 🚀 快速开始

### 方式一：FPK 部署（推荐 - 飞牛 NAS/Docker 用户）

1. **下载 FPK 包**
   ```bash
   # 克隆仓库
   git clone https://github.com/yanfeng17/Good-GYM.git
   cd Good-GYM/fpk
   ```

2. **安装到 FNOS**
   - 在飞牛 OS 应用商店中选择"本地安装"
   - 上传 `goodgym.fpk` 文件
   - 安装完成后，在浏览器访问 `http://[NAS_IP]:6080`

### 方式二：Docker 部署

```bash
# 1. 克隆仓库
git clone https://github.com/yanfeng17/Good-GYM.git
cd Good-GYM

# 2. 配置摄像头地址（可选）
# 编辑 docker-compose.yml 修改 RTSP URL

# 3. 启动容器
docker-compose up -d

# 4. 访问应用
# 浏览器打开: http://localhost:6080
```

### 方式三：本地 Python 运行

```bash
# 1. 克隆仓库
git clone https://github.com/yanfeng17/Good-GYM.git
cd Good-GYM

# 2. 创建虚拟环境
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行应用
python run.py
```

## 📋 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|---------|---------|
| **操作系统** | Windows 10 / macOS 10.15 / Linux | Windows 11 / macOS 12+ / Ubuntu 20.04+ |
| **Python** | 3.9 | 3.9 或 3.10 |
| **CPU** | 双核 2GHz | 四核 3GHz+ |
| **内存** | 4GB | 8GB+ |
| **摄像头** | 任意 USB/网络摄像头 | 1080p 摄像头 |
| **Docker** (可选) | Docker 20.10+ | Docker 24.0+ |

## 🎮 使用指南

### 1. Web 界面操作

访问 `http://[设备IP]:6080` 进入 Web 界面：

- **🎥 视频显示区** - 实时显示摄像头画面和骨骼追踪
- **📊 控制面板** - 选择运动类型、调整设置
- **🔊 音频状态** - 右上角显示音频连接状态（绿色=已连接）
- **🎯 计数显示** - 大字显示当前次数

### 2. 支持的运动类型

| 运动类型 | 中文名称 | 关键点检测 |
|---------|---------|----------|
| `squat` | 深蹲 | 髋-膝-踝角度 |
| `pushup` | 俯卧撑 | 肩-肘-腕角度 |
| `situp` | 仰卧起坐 | 肩-髋-膝角度 |
| `bicep_curl` | 哑铃弯举 | 肩-肘-腕角度 |
| `lateral_raise` | 侧平举 | 肩-手腕角度 |
| `overhead_press` | 推举 | 肩-肘-腕角度 |
| `leg_raise` | 抬腿 | 髋-膝-踝角度 |
| `knee_raise` | 提膝 | 髋-膝-踝角度 |
| `knee_press` | 膝盖俯卧撑 | 肩-肘-膝角度 |
| `crunch` | 卷腹 | 肩-髋-膝角度 |

### 3. 自定义运动类型

编辑 `data/exercises.json` 添加新运动：

```json
{
  "my_exercise": {
    "name_zh": "我的运动",
    "name_en": "My Exercise",
    "down_angle": 90,
    "up_angle": 170,
    "keypoints": {
      "left": [11, 13, 15],
      "right": [12, 14, 16]
    },
    "is_leg_exercise": false,
    "angle_point": [12, 14, 16]
  }
}
```

**参数说明：**
- `down_angle`: 下放阶段的角度阈值（度）
- `up_angle`: 上升阶段的角度阈值（度）
- `keypoints.left/right`: 左右两侧的三个关节点索引
- `is_leg_exercise`: 是否为腿部运动
- `angle_point`: 用于绘制角度指示的三个点

MediaPipe 关键点索引：
- 头部: 0-10
- 上肢: 11(左肩), 12(右肩), 13(左肘), 14(右肘), 15(左腕), 16(右腕)
- 下肢: 23(左髋), 24(右髋), 25(左膝), 26(右膝), 27(左踝), 28(右踝)

### 4. RTSP 摄像头配置

在 `docker-compose.yml` 中修改 RTSP URL：

```yaml
services:
  goodgym:
    environment:
      - RTSP_URL=rtsp://用户名:密码@摄像头IP:端口/stream
```

或在 Web 界面的"控制面板"中实时修改。

## 🏗️ 项目架构

```
Good-GYM/
├── app/                    # 主应用模块
│   ├── main_window.py      # 主窗口逻辑
│   ├── video_processor.py  # 视频处理
│   └── video_source_manager.py  # 视频源管理
├── core/                   # 核心功能模块
│   ├── pose_processor.py   # MediaPipe 姿态处理
│   ├── sound_manager.py    # 音频管理
│   ├── settings_manager.py # 设置持久化
│   ├── stats_manager.py    # 统计数据管理
│   └── ha_api_manager.py   # Home Assistant API
├── ui/                     # UI 组件
│   ├── control_panel.py    # 控制面板
│   ├── video_display.py    # 视频显示
│   └── styles.py           # 样式定义
├── assets/                 # 资源文件
│   ├── count.mp3           # 计数音效
│   ├── milestone.mp3       # 里程碑音效（金币）
│   └── succeed.mp3         # 成功音效
├── data/                   # 数据目录
│   ├── exercises.json      # 运动类型配置
│   ├── user_settings.json  # 用户设置（自动生成）
│   └── tts_config.json     # TTS 配置
├── models/                 # AI 模型文件
│   ├── pose_landmarker_lite.task
│   ├── pose_landmarker_full.task
│   └── pose_landmarker_heavy.task
├── fpk/                    # FPK 打包目录
├── audio_ws_server.py      # WebSocket 音频服务器
├── vnc_audio.html          # Web 音频界面
├── Dockerfile              # Docker 镜像定义
├── docker-compose.yml      # Docker Compose 配置
├── supervisord.conf        # Supervisor 进程管理
└── requirements.txt        # Python 依赖
```

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| **姿态检测** | MediaPipe Pose Landmarker |
| **UI 框架** | PyQt5 |
| **视频处理** | OpenCV |
| **Web 服务** | noVNC, WebSocket |
| **音频** | Web Audio API, Web Speech Synthesis |
| **容器化** | Docker, Docker Compose |
| **进程管理** | Supervisor |
| **桌面环境** | Xvfb, Fluxbox, X11VNC |

## 📊 功能详解

### 语音播报

- **桌面端（支持 TTS）**：语音播报次数（如"5"、"10"）
- **移动端（不支持 TTS）**：播放音效文件
- **里程碑音效**：每 10 次（10、20、30...）播放金币掉落音效

### 设置持久化

以下设置会自动保存到 `data/user_settings.json`：
- 运动类型
- RTSP 摄像头地址
- 视频源类型
- 镜像模式
- TTS 模式

容器重启后自动恢复上次配置。

### 端口说明

| 端口 | 用途 |
|------|-----|
| **6080** | Web 主界面（带音频） |
| **6081** | noVNC 界面（无音频） |
| **8765** | WebSocket 音频流 |

## 🤝 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📝 常见问题

<details>
<summary><strong>Q: 为什么移动端没有声音？</strong></summary>

A: 移动浏览器的音频播放受限。请在页面加载后点击任意位置以激活音频引擎。系统会自动尝试解锁音频。
</details>

<details>
<summary><strong>Q: Docker 容器启动失败？</strong></summary>

A: 请检查：
1. Docker 是否正常运行
2. 端口 6080/6081/8765 是否被占用
3. RTSP 摄像头地址是否正确
</details>

<details>
<summary><strong>Q: 如何更换音效文件？</strong></summary>

A: 将您的 MP3 文件替换 `assets/` 目录下的对应文件：
- `count.mp3` - 普通计数音效
- `milestone.mp3` - 里程碑音效
- `succeed.mp3` - 成功音效
</details>

## 🙏 致谢

- [Google MediaPipe](https://mediapipe.dev/) - AI 姿态检测
- [RTMPose](https://github.com/Tau-J/rtmlib) - 姿态检测模型参考
- [noVNC](https://github.com/novnc/noVNC) - Web VNC 实现

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

---

<div align="center">

**如果这个项目对您有帮助，请给它一个 ⭐️**

Made with ❤️ by [yanfeng17](https://github.com/yanfeng17)

</div>
