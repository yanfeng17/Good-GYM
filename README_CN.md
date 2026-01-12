# Good-GYM: AI健身助手 💪

<div align="center">

<img src="assets/Logo-ch.png" width="200px" alt="Good-GYM 标志">

[![GitHub stars](https://img.shields.io/github/stars/yo-WASSUP/Good-GYM?style=social)](https://github.com/yo-WASSUP/Good-GYM/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/yo-WASSUP/Good-GYM?style=social)](https://github.com/yo-WASSUP/Good-GYM/network/members)
[![GitHub license](https://img.shields.io/github/license/yo-WASSUP/Good-GYM)](https://github.com/yo-WASSUP/Good-GYM/blob/main/LICENSE)

**基于MediaPipe姿态检测的AI健身助手**

[English](README.md) | [中文](README_CN.md)

[![小红书视频介绍](https://img.shields.io/badge/小红书-视频介绍-ff2442)](https://www.xiaohongshu.com/explore/6808b102000000001c0157ad?xsec_token=ABm-Sdk88be4nJCaCVfCI9gQahnLiKt16mUC3gbupYH3g=&xsec_source=pc_user)

</div>

## 🆕 更新日志

- **2026-01-09**：重大更新！迁移到 MediaPipe 姿态检测，解决 ONNX Runtime DLL 依赖问题，提升跨平台兼容性和稳定性。
- **2025-11-15**：新增运动类型数据库功能！所有运动配置现在统一管理在 `data/exercises.json` 文件中，支持自定义添加、修改运动类型，无需修改代码。
- **2025-11-14**：由于异步姿态检测存在准确率问题，已恢复到同步姿态检测。修复了从统计界面切换回检测界面时闪退的问题。
- **2025-06-12**：优化exercise_counters.py，提高计数准确性，代码结构优化

## 🔮 开发计划

- [x] 多语言界面
- [x] 提高姿势检测精度
- [x] 添加对更多锻炼类型的支持
- [x] 添加自定义锻炼模板
- [ ] 识别动作准确性
- [ ] 动作纠错提示
- [ ] 添加语音交互控制
- [ ] 移动应用程序支持

---
<img src="assets/demo.gif" width="800px" alt="演示">

<img src="assets/demo-status.gif" width="800px" alt="演示">

## ✨ 功能特点

- **实时运动计数** - 自动计算您的健身次数
- **多种运动支持** - 包括深蹲、俯卧撑、仰卧起坐、哑铃运动等十多种
- **先进的姿态检测** - 采用 Google MediaPipe 实现精准跟踪
- **零依赖** - 无需 GPU 或额外 DLL，安装简单，跨平台兼容
- **可视化反馈** - 实时骨骼可视化和角度测量
- **健身统计** - 跟踪您的健身进度
- **用户友好界面** - 基于PyQt5的简洁界面，操作直观
- **兼容普通摄像头** - 无需特殊硬件
- **本地运行** - 完全隐私

## 📋 系统要求

- Python 3.9
- 摄像头
- **Windows/Mac/Linux**: 仅需CPU，无需GPU。性能取决于硬件。

## 📦 快速下载

- 如果您不想配置Python环境，可以直接下载我们打包好的可执行文件：

  **Windows EXE打包版本**：

  [百度网盘链接]( https://pan.baidu.com/s/1xzZjwUmnXLaWatqPcSE1zw ) 提取码: 8866

  [Google Drive](https://drive.google.com/file/d/1VKDecEDLdnyi59ZmHhOvUPwAxxkw9wlH/view?usp=drive_link)

## 📝 使用指南

### 控制方式

- 使用界面按钮选择不同的运动类型
- 实时反馈显示您当前的姿势和重复次数
- 按"重置"按钮重置计数器
- 使用手动调整按钮修正计数(如有需要)
- 开关骨骼可视化
- 查看您的健身统计数据

### 🎯 自定义运动类型

现在所有运动类型都存储在 `data/exercises.json` 文件中，您可以轻松添加、修改或删除运动类型，无需修改代码！

#### 如何添加新运动类型

1. **关节点索引说明**
   - 系统使用 MediaPipe 33 关键点格式，主要关节点索引对应关系：
     - `0`: 鼻子, `1-10`: 面部关键点
     - `11`: 左肩, `12`: 右肩, `13`: 左肘, `14`: 右肘
     - `15`: 左手腕, `16`: 右手腕, `17-22`: 手部关键点
     - `23`: 左臀, `24`: 右臀, `25`: 左膝, `26`: 右膝
     - `27`: 左脚踝, `28`: 右脚踝, `29-32`: 脚部关键点

2. **配置参数说明**
   - `down_angle`: 动作下放时的角度阈值（度）
   - `up_angle`: 动作上升时的角度阈值（度）
   - `keypoints.left`: 左侧三个关节点索引 [点1, 点2, 点3]，用于计算角度
   - `keypoints.right`: 右侧三个关节点索引 [点1, 点2, 点3]，用于计算角度
   - `is_leg_exercise`: 是否为腿部运动（true/false），影响计数逻辑
   - `angle_point`: 用于显示的角度点索引 [点1, 点2, 点3]，在视频上绘制角度线

3. **添加新运动示例**
   ```json
   "my_custom_exercise": {
     "name_zh": "我的自定义运动",
     "name_en": "My Custom Exercise",
     "down_angle": 120,
     "up_angle": 170,
     "keypoints": {
       "left": [5, 7, 9],
       "right": [6, 8, 10]
     },
     "is_leg_exercise": false,
     "angle_point": [6, 8, 10]
   }
   ```

4. **重启程序**
   - 保存文件后，重启程序即可看到新添加的运动类型

## 🚀 安装指南

### 安装方法

1. **克隆并安装**
   ```bash
   git clone https://github.com/yo-WASSUP/Good-GYM.git
   cd Good-GYM
   
   # 创建虚拟环境
   python -m venv venv
   # Windows激活
   .\venv\Scripts\activate
   # 或 (Mac/Linux)
   source venv/bin/activate
   
   # 安装依赖
   pip install -r requirements.txt
   ```

2. **运行应用**
   ```bash
   python run.py
   ```

## 🖼️ 应用截图

<img src="assets/Screenshot-ch-1.png" width="600px" alt="截图1">

<img src="assets/Screenshot-ch-2.png" width="600px" alt="截图2">

<img src="assets/Screenshot-ch-3.png" width="600px" alt="截图3">

<img src="assets/Screenshot-ch-4.png" width="600px" alt="截图4">

<img src="assets/Screenshot-ch-5.png" width="600px" alt="截图5">

## 🤝 贡献

欢迎贡献代码！请随时提交Pull Request。

感谢RTMPose开源姿态检测模型： https://github.com/Tau-J/rtmlib

## 📄 许可证

本项目采用MIT许可证 - 详情请参阅LICENSE文件。
