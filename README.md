# Good-GYM: AI Fitness Assistant 💪

<div align="center">

<img src="assets/Logo.png" width="200px" alt="Good-GYM Logo">

[![GitHub stars](https://img.shields.io/github/stars/yo-WASSUP/Good-GYM?style=social)](https://github.com/yo-WASSUP/Good-GYM/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/yo-WASSUP/Good-GYM?style=social)](https://github.com/yo-WASSUP/Good-GYM/network/members)
[![GitHub license](https://img.shields.io/github/license/yo-WASSUP/Good-GYM)](https://github.com/yo-WASSUP/Good-GYM/blob/main/LICENSE)

**AI Fitness Assistant Based on RTMPose**

[English](README.md) | [中文](README_CN.md)

[![LinkedIn introduction](https://img.shields.io/badge/LinkedIn-介绍-0077B5)](https://www.linkedin.com/posts/huihuang-tang_ai-computervision-opencv-activity-7325469166591770624-Bbyx?utm_source=share&utm_medium=member_desktop&rcm=ACoAAD7qaoMBbw89mcxb0dNh_O4ezc8EFShoOtU)

</div>

## 🆕 Changelog

- **2025-06-07**: Major update! Dropped YOLO models and all GPU support. Now uses only RTMPose for pose detection, and runs on CPU only. Simpler, more compatible, and easier to use.
- **2025-06-12**：Optimize exercise_counters.py for counting accuracy, code structure optimization
- **2025-11-14**: Reverted asynchronous pose detection due to accuracy issues, restored synchronous pose detection. Fixed crash when switching from statistics mode back to detection mode.
- **2025-11-15**: New exercise database feature! All exercise configurations are now managed in `data/exercises.json` file. You can easily add, modify, or remove exercise types without modifying code.

## 🔮 Future Development

- [x] Multi-language interface
- [x] Improve pose detection accuracy
- [ ] Add support for more exercise types
- [ ] Add custom exercise types template
- [ ] Recognizing Motion Accuracy
- [ ] Motion Error Correction Indication
- [ ] Add voice feedback
- [ ] Mobile Application Support


---
<img src="assets/demo-en.gif" width="800px" alt="演示">

<img src="assets/demo-status-en.gif" width="800px" alt="演示">

## 🌟 Features

- **Real-time Exercise Counting** - Automatically counts your repetitions
- **Multiple Exercise Support** - Including squats, push-ups, sit-ups, bicep curls, and many more
- **Advanced Pose Detection** - Powered by RTMPose for accurate tracking
- **CPU Only** - No GPU required, works on most computers
- **Visual Feedback** - Live skeleton visualization with angle measurements
- **Workout Statistics** - Track your progress over time
- **User-friendly Interface** - Clean PyQt5 GUI with intuitive controls
- **Works with any webcam** - No special hardware required
- **Runs locally** - Complete privacy

## 📦 Direct Download
- If you don't want to set up a Python environment, you can download our pre-packaged executable:

  **Windows EXE package**: 

  [Baidu Netdisk Link](https://pan.baidu.com/s/1xzZjwUmnXLaWatqPcSE1zw) code: 8866

  [Google Drive](https://drive.google.com/file/d/1VKDecEDLdnyi59ZmHhOvUPwAxxkw9wlH/view?usp=drive_link)

## 📝 Usage Guide

### Controls

- Use the interface buttons to select different exercises
- Real-time feedback shows your current form and repetition count
- Press the "Reset" button to reset the counter
- Use manual adjustment buttons to correct the count if needed
- Toggle skeleton visualization on/off
- View your workout statistics over time

### 🎯 Custom Exercise Types

All exercise types are now stored in the `data/exercises.json` file. You can easily add, modify, or remove exercise types without modifying code!

#### How to Add a New Exercise Type

1. **Keypoint Index Reference**
   - The system uses COCO 17 keypoint format:
     - `0`: nose, `1`: left_eye, `2`: right_eye, `3`: left_ear, `4`: right_ear
     - `5`: left_shoulder, `6`: right_shoulder, `7`: left_elbow, `8`: right_elbow
     - `9`: left_wrist, `10`: right_wrist, `11`: left_hip, `12`: right_hip
     - `13`: left_knee, `14`: right_knee, `15`: left_ankle, `16`: right_ankle

2. **Configuration Parameters**
   - `down_angle`: Angle threshold when lowering (degrees)
   - `up_angle`: Angle threshold when raising (degrees)
   - `keypoints.left`: Left side three keypoint indices [pt1, pt2, pt3] for angle calculation
   - `keypoints.right`: Right side three keypoint indices [pt1, pt2, pt3] for angle calculation
   - `is_leg_exercise`: Whether it's a leg exercise (true/false), affects counting logic
   - `angle_point`: Keypoint indices [pt1, pt2, pt3] for displaying angle lines on video

3. **Example: Adding a New Exercise**
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

4. **Restart the Application**


## 📋 Requirements

- Python 3.9
- Webcam
- **Windows/Mac/Linux**: CPU only, no GPU required. Performance may vary by hardware.

## 🚀 Environment Setup

### Installation

1. **Clone and install**
   ```bash
   git clone https://github.com/yo-WASSUP/Good-GYM.git
   cd Good-GYM
   
   # Create virtual environment
   python -m venv venv
   # Activate (Windows)
   .\venv\Scripts\activate
   # or (Mac/Linux)
   source venv/bin/activate
   
   # Install dependencies
   pip install -r requirements.txt
   ```

2. **Run the application**
   ```bash
   python workout_qt_modular.py
   ```

## 🖼️ Screenshots

<img src="assets/Screenshot-en-1.png" width="600px" alt="Screenshot 1">

<img src="assets/Screenshot-en-2.png" width="600px" alt="Screenshot 2">

<img src="assets/Screenshot-en-3.png" width="600px" alt="Screenshot 3">

<img src="assets/Screenshot-en-4.png" width="600px" alt="Screenshot 4">

<img src="assets/Screenshot-en-5.png" width="600px" alt="Screenshot 5">

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

Thanks to RTMPose open source pose detection model: https://github.com/Tau-J/rtmlib

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

