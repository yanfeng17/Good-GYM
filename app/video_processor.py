"""
视频处理模块 - 负责图像更新和姿态检测
"""

import cv2
import os
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QTimer
from core.translations import Translations as T

class VideoProcessor:
    """视频处理器类"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def update_image(self, frame, fps=0):
        """更新图像显示并处理姿态检测"""
        try:
            # 添加调试计数器
            if not hasattr(self, 'debug_frame_counter'):
                self.debug_frame_counter = 0
            self.debug_frame_counter += 1
            
            # 每100帧打印一次调试信息
            if self.debug_frame_counter % 100 == 0:
                print(f"[VideoProcessor] 已处理 {self.debug_frame_counter} 帧, FPS={fps:.1f}")
            
            # 更新FPS值
            self.main_window.current_fps = fps
            
            # 如果 MediaPipe 还未初始化，只显示原始帧
            if self.main_window.pose_processor is None:
                # 转换BGR到RGB（Qt需要RGB格式）
                display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                self.main_window.video_display.update_image(display_frame)
                return
            
            # 跳帧机制：初始化计数器
            if not hasattr(self, 'frame_skip_counter'):
                self.frame_skip_counter = 0
                self.last_keypoints = None
                self.last_angle = None
                self.last_angle_point = None
            
            self.frame_skip_counter += 1
            # 每2帧才处理一次MediaPipe
            should_process = (self.frame_skip_counter % 2 == 0)
            
            # 使用推理帧进行姿态检测
            inference_frame = getattr(self.main_window, 'current_inference_frame', frame)
            
            # 根据是否需要处理来决定
            if should_process:
                # 姿态处理器处理推理帧
                _, current_angle, angle_point, keypoints = self.main_window.pose_processor.process_frame(
                    inference_frame, self.main_window.exercise_type
                )
                # 保存结果
                self.last_keypoints = keypoints
                self.last_angle = current_angle
                self.last_angle_point = angle_point
            else:
                # 使用上一帧的结果
                keypoints = self.last_keypoints
                current_angle = self.last_angle
                angle_point = self.last_angle_point
            
            # 准备高分辨率显示帧
            display_frame = frame.copy()
            
            # 计算缩放比例（推理帧到显示帧）
            scale_x = display_frame.shape[1] / inference_frame.shape[1]
            scale_y = display_frame.shape[0] / inference_frame.shape[0]
            
            # 如果有关键点信息，在高分辨率帧上绘制骨架
            if keypoints is not None and self.main_window.pose_processor.show_skeleton:
                # 将关键点坐标缩放到显示帧尺寸
                scaled_keypoints = keypoints.copy()
                scaled_keypoints[:, 0] *= scale_x
                scaled_keypoints[:, 1] *= scale_y
                
                # 在高分辨率帧上绘制骨架
                display_frame = self.draw_skeleton_on_frame(display_frame, scaled_keypoints)
            
            # 先缩放角度点坐标（基于推理帧尺寸）
            if angle_point is not None and len(angle_point) == 3:
                # 先缩放到显示帧尺寸
                scaled_angle_point = [
                    [int(angle_point[0][0] * scale_x), int(angle_point[0][1] * scale_y)],
                    [int(angle_point[1][0] * scale_x), int(angle_point[1][1] * scale_y)],
                    [int(angle_point[2][0] * scale_x), int(angle_point[2][1] * scale_y)]
                ]
            else:
                scaled_angle_point = None
            
            # 如果启用镜像模式，先应用镜像处理
            if self.main_window.mirror_mode:
                display_frame = cv2.flip(display_frame, 1)
                # 镜像后需要调整角度点坐标（因为显示帧被镜像了）
                if scaled_angle_point is not None:
                    frame_width = display_frame.shape[1]
                    # 镜像 x 坐标：frame_width - x
                    scaled_angle_point = [
                        [int(frame_width - scaled_angle_point[0][0]), scaled_angle_point[0][1]],
                        [int(frame_width - scaled_angle_point[1][0]), scaled_angle_point[1][1]],
                        [int(frame_width - scaled_angle_point[2][0]), scaled_angle_point[2][1]]
                    ]
            
            # 在镜像后绘制角度线（这样角度线位置就正确了）
            if scaled_angle_point is not None:
                display_frame = self.draw_angle_lines(display_frame, scaled_angle_point, current_angle)
            
            # 转换BGR到RGB（Qt需要RGB格式）
            display_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            
            # 更新视频显示
            self.main_window.video_display.update_image(display_frame)
            
            # 更新UI组件
            self.update_ui_components(current_angle, keypoints)
            
        except Exception as e:
            print(f"Error updating image: {e}")
    
    def draw_skeleton_on_frame(self, frame, keypoints):
        """在高分辨率帧上绘制骨架（不显示面部）"""
        try:
            # 定义连接关系 (MediaPipe 33 keypoint format) - 排除面部连接
            connections = [
                # 躯干
                [11, 12],  # 左肩-右肩
                [11, 23], [12, 24],  # 肩-臀
                [23, 24],  # 左臀-右臀  
                # 手臂
                [11, 13], [13, 15],  # 左肩-左肘-左手腕
                [15, 17], [15, 19], [15, 21],  # 左手指
                [12, 14], [14, 16],  # 右肩-右肘-右手腕
                [16, 18], [16, 20], [16, 22],  # 右手指
                # 腿部
                [23, 25], [25, 27],  # 左臀-左膝-左脚踝
                [27, 29], [27, 31],  # 左脚
                [24, 26], [26, 28],  # 右臀-右膝-右脚踝
                [28, 30], [28, 32]   # 右脚
            ]
            
            # 定义颜色 (BGR format)
            colors = {
                'torso': (255, 153, 51),   # Orange
                'arms': (153, 255, 51),    # Green
                'legs': (255, 51, 153)     # Pink
            }
            
            # 绘制连接线
            for connection in connections:
                pt1_idx, pt2_idx = connection
                if pt1_idx < len(keypoints) and pt2_idx < len(keypoints):
                    pt1 = keypoints[pt1_idx]
                    pt2 = keypoints[pt2_idx]
                    
                    # 跳过无效点
                    if (pt1[0] == 0 and pt1[1] == 0) or (pt2[0] == 0 and pt2[1] == 0):
                        continue
                    
                    # 选择颜色（MediaPipe 33 关键点）- 不包含面部
                    if pt1_idx in [11, 12, 23, 24]:  # 躯干
                        color = colors['torso']
                    elif pt1_idx in [13, 14, 15, 16, 17, 18, 19, 20, 21, 22]:  # 手臂和手
                        color = colors['arms']
                    else:  # 腿部 (25-32)
                        color = colors['legs']
                    
                    # 绘制连接线 - 根据分辨率调整线条粗细
                    line_thickness = max(2, int(frame.shape[1] / 640 * 3))
                    cv2.line(frame, 
                            (int(pt1[0]), int(pt1[1])), 
                            (int(pt2[0]), int(pt2[1])), 
                            color, line_thickness)
            
            # 绘制关键点 - 跳过面部关键点 (0-10)
            for i, point in enumerate(keypoints):
                # 跳过面部关键点
                if i < 11:
                    continue
                    
                # 跳过无效点
                if point[0] == 0 and point[1] == 0:
                    continue
                
                # 选择颜色（MediaPipe 33 关键点）
                if i in [11, 12, 23, 24]:  # 躯干
                    color = colors['torso']
                elif i in [13, 14, 15, 16, 17, 18, 19, 20, 21, 22]:  # 手臂和手
                    color = colors['arms']
                else:  # 腿部 (25-32)
                    color = colors['legs']
                
                # 根据分辨率调整关键点大小
                point_radius = max(3, int(frame.shape[1] / 640 * 5))
                cv2.circle(frame, (int(point[0]), int(point[1])), point_radius, color, -1)
                cv2.circle(frame, (int(point[0]), int(point[1])), point_radius + 2, color, 2)
            
            return frame
            
        except Exception as e:
            print(f"Error drawing skeleton: {e}")
            return frame
    
    def draw_angle_lines(self, frame, angle_point, angle_value):
        """在帧上绘制角度线和角度值"""
        try:
            if angle_point is None or len(angle_point) != 3:
                return frame
            
            pt1, pt2, pt3 = angle_point
            
            # 检查点是否有效（不是 (0, 0) 且在帧范围内）
            frame_height, frame_width = frame.shape[:2]
            if (pt1[0] == 0 and pt1[1] == 0) or (pt2[0] == 0 and pt2[1] == 0) or (pt3[0] == 0 and pt3[1] == 0):
                return frame
            
            # 检查坐标是否在有效范围内（防止坐标超出帧范围导致绘制到错误位置）
            if (pt1[0] < 0 or pt1[0] >= frame_width or pt1[1] < 0 or pt1[1] >= frame_height or
                pt2[0] < 0 or pt2[0] >= frame_width or pt2[1] < 0 or pt2[1] >= frame_height or
                pt3[0] < 0 or pt3[0] >= frame_width or pt3[1] < 0 or pt3[1] >= frame_height):
                # 坐标超出范围，不绘制
                return frame
            
            # 定义角度线颜色（黄色，BGR格式）
            angle_color = (0, 255, 255)  # Yellow
            
            # 根据分辨率调整线条粗细
            line_thickness = max(2, int(frame.shape[1] / 640 * 2))
            
            # 绘制两条角度线：pt1-pt2 和 pt2-pt3
            cv2.line(frame, (pt1[0], pt1[1]), (pt2[0], pt2[1]), angle_color, line_thickness)
            cv2.line(frame, (pt2[0], pt2[1]), (pt3[0], pt3[1]), angle_color, line_thickness)
            
            # 在中间点（pt2）绘制一个小圆圈
            circle_radius = max(4, int(frame.shape[1] / 640 * 6))
            cv2.circle(frame, (pt2[0], pt2[1]), circle_radius, angle_color, -1)
            
            # 在角度点附近显示角度值（如果角度值有效）
            if angle_value is not None:
                # 计算文本位置（在中间点上方）
                text_x = pt2[0]
                text_y = pt2[1] - 20
                
                # 确保文本位置在帧内
                if text_y < 20:
                    text_y = pt2[1] + 30
                
                # 绘制角度值文本（使用数字和deg避免特殊字符显示问题）
                font_scale = max(0.5, frame.shape[1] / 640 * 0.6)
                # 使用 "deg" 代替度符号，避免显示问题
                text = f"{int(angle_value)} deg"
                cv2.putText(frame, text, (text_x, text_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, font_scale, angle_color, 2)
            
            return frame
            
        except Exception as e:
            print(f"Error drawing angle lines: {e}")
            return frame
    
    def update_ui_components(self, current_angle, keypoints):
        """更新UI组件显示"""
        try:
            # 更新角度显示 - 注释掉这部分代码
            # if current_angle is not None:
            #     self.main_window.control_panel.update_angle(str(int(current_angle)), self.main_window.exercise_type)
            
            # 更新阶段显示（上/下）
            if hasattr(self.main_window.exercise_counter, 'stage'):
                self.main_window.control_panel.update_phase(self.main_window.exercise_counter.stage)
            
            # 获取当前计数
            current_count = self.main_window.exercise_counter.counter
            
            # 只有当计数增加时才更新（用于避免重复更新）
            if current_count > self.main_window.current_count and not self.main_window.is_resetting:
                # TTS语音播报（包含音效）
                exercise_name = self.main_window.control_panel.exercise_display_map.get(
                    self.main_window.exercise_type, 
                    self.main_window.exercise_type
                )
                self.main_window.announce_count(current_count, exercise_name)
                
                # 达到里程碑（10的倍数）时特殊提示
                if current_count % 10 == 0:
                    self.main_window.statusBar.showMessage(f"Congratulations on completing {current_count} {self.main_window.control_panel.exercise_display_map[self.main_window.exercise_type]}!")
                
                # 更新当前计数
                self.main_window.current_count = current_count
            
            # 更新UI显示的计数器
            self.main_window.control_panel.update_counter(str(current_count))
        except Exception as e:
            print(f"Error updating image: {str(e)}")
    
    def change_camera(self, index):
        """切换摄像头"""
        self.main_window.video_thread.set_camera(index)
        self.main_window.statusBar.showMessage(f"Switched to camera {index}")
    
    def toggle_rotation(self, rotate):
        """切换视频旋转模式"""
        # 更新视频线程旋转设置
        self.main_window.video_thread.set_rotation(rotate)
        
        # 更新视频显示方向设置
        # rotate=True表示竖屏，False表示横屏
        self.main_window.video_display.set_orientation(portrait_mode=rotate)
        
        if rotate:
            self.main_window.toggle_rotation_action.setText("Turn off rotation mode")
            self.main_window.statusBar.showMessage("Switched to portrait mode (9:16)")
        else:
            self.main_window.toggle_rotation_action.setText("Turn on rotation mode")
            self.main_window.statusBar.showMessage("Switched to landscape mode (16:9)")
    
    def toggle_skeleton(self, show):
        """切换骨架显示"""
        self.main_window.pose_processor.set_skeleton_visibility(show)
        if show:
            self.main_window.statusBar.showMessage("Show skeleton lines")
        else:
            self.main_window.statusBar.showMessage("Hide skeleton lines")
    
    def toggle_mirror(self, mirror):
        """切换镜像模式"""
        self.main_window.mirror_mode = mirror
        # 同步更新 video_thread 的镜像设置
        if hasattr(self.main_window, 'video_thread'):
            self.main_window.video_thread.set_mirror(mirror)
        self.main_window.statusBar.showMessage(f"Mirror mode: {'ON' if mirror else 'OFF'}")
        
        # 更新菜单动作状态
        if hasattr(self.main_window, 'toggle_mirror_action'):
            self.main_window.toggle_mirror_action.setChecked(mirror)
    
    def open_video_file(self):
        """打开视频文件"""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self.main_window,
            T.get("open_video"),
            "",
            T.get("video_files"),
            options=options
        )
        
        if file_name:
            try:
                # 清除当前计数状态
                self.main_window.reset_exercise_state()
                
                # 切换到运动模式（如果当前不是）
                if hasattr(self.main_window, 'stacked_layout') and hasattr(self.main_window, 'exercise_container'):
                    if not self.main_window.stacked_layout.currentWidget() == self.main_window.exercise_container:
                        self.main_window.switch_to_workout_mode()
                
                # 设置状态栏信息
                video_name = os.path.basename(file_name)
                self.main_window.statusBar.showMessage(f"Current video: {video_name}")
                
                # 将文件路径传递给视频线程，设置为非循环播放模式
                self.main_window.video_thread.set_video_file(file_name, loop=False)
            except Exception as e:
                print(f"Error opening video file: {e}")
                self.main_window.statusBar.showMessage(f"Failed to open video file: {str(e)}")
    
    def switch_to_camera_mode(self):
        """切换回摄像头模式"""
        try:
            # 清除当前计数状态
            self.main_window.reset_exercise_state()
            
            # 切换到运动模式（如果当前不是）
            if hasattr(self.main_window, 'stacked_layout') and hasattr(self.main_window, 'exercise_container'):
                if not self.main_window.stacked_layout.currentWidget() == self.main_window.exercise_container:
                    self.main_window.switch_to_workout_mode()
                
            # 设置状态栏信息
            self.main_window.statusBar.showMessage("Current mode: Camera")
            
            # 返回摄像头模式
            self.main_window.video_thread.set_camera(0)  # 使用默认摄像头
        except Exception as e:
            print(f"Error switching to camera mode: {e}")
            self.main_window.statusBar.showMessage(f"Failed to switch to camera mode: {str(e)}")