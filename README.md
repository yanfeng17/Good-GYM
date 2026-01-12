# Good-GYM: AI健身助手 💪

<div align="center">

![Good-GYM Logo](fpk/ICON.PNG)

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

## 🎥 摄像头配置指南

### 1. 本地 USB 摄像头
- **Windows/Linux**: 默认使用系统识别到的第一个摄像头（ID=0）。无需配置，即插即用。
- **Docker**: 一般无法直接使用宿主机 USB 摄像头（除非直通），推荐使用 RTSP 网络摄像头。

### 2. RTSP 网络摄像头（推荐）

#### 常见品牌 RTSP 地址格式：
- **海康威视 (Hikvision)**:
  `rtsp://admin:密码@IP地址:554/h264/ch1/main/av_stream`
- **TP-Link / TAPO**:
  `rtsp://admin:密码@IP地址:554/stream1`
- **小米/大方**:
  `rtsp://IP地址:8554/unicast`

#### 如何配置：
1. **Web 界面配置**：
   - 打开 Good-GYM 网页 (`http://IP:6080`)
   - 点击右下角【控制面板】
   - 将【视频源】选择为 `RTSP`
   - 在下方输入框填入完整 RTSP 地址
   - 点击【保存设置】，页面会自动刷新

2. **配置文件配置 (Docker)**:
   - 修改 `docker-compose.yml`:
     ```yaml
     environment:
       - RTSP_URL=rtsp://admin:password@192.168.1.100:554/stream1
     ```

### 3. 使用手机作为摄像头
- **iOS/Android**: 安装 "IP Webcam" 或 "DroidCam" 应用。
- 获取 RTSP/HTTP 流地址（例如 `http://192.168.1.5:8080/video`）。
- 在 Good-GYM 中填写该地址。

## 🚀 快速开始

### 方式一：FPK 部署（推荐 - 飞牛 NAS/Docker 用户）

1. **下载 FPK 包**
   ```bash
   git clone https://github.com/yanfeng17/Good-GYM.git
   ```

2. **安装到 FNOS**
   - 在飞牛 OS 应用商店中选择"本地安装"
   - 上传 `fpk/goodgym.fpk` 文件
   - 安装完成后，在浏览器访问 `http://[NAS_IP]:6080`

### 方式二：Docker 部署

```bash
docker-compose up -d
```

### 方式三：本地 Python 运行

```bash
pip install -r requirements.txt
python run.py
```

## 📋 系统要求

| 项目 | 最低要求 | 推荐配置 |
|------|---------|---------|
| **操作系统** | Windows 10 / macOS 10.15 / Linux | Windows 11 / macOS 12+ / Ubuntu 20.04+ |
| **Python** | 3.9 | 3.9 或 3.10 |
| **摄像头** | 任意 USB/网络摄像头 | 1080p 摄像头 |
| **Docker** | Docker 20.10+ | Docker 24.0+ |

## 🎮 使用指南

### 1. Web 界面操作
访问 `http://[设备IP]:6080`：
- **🎥 视频显示区** - 实时显示摄像头画面和骨骼追踪
- **📊 控制面板** - 选择运动类型、调整设置
- **🔊 音频状态** - 右上角显示音频连接状态（绿色=已连接）
- **🎯 计数显示** - 大字显示当前次数

### 2. 支持的运动类型
(深蹲、俯卧撑、仰卧起坐等 10+ 种)

## 🤝 贡献指南
欢迎提交 Pull Request！

## 📄 许可证
[MIT License](LICENSE)

---
<div align="center">Made with ❤️ by yanfeng17</div>
