import os
import cv2
import sys
import numpy as np
import json
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class PoseProcessor:
    """MediaPipe 姿态检测处理器"""
    
    def __init__(self, exercise_counter, model_version='lite'):
        self.exercise_counter = exercise_counter
        self.show_skeleton = True
        self.conf_threshold = 0.5
        self.model_version = model_version
        
        # 初始化 MediaPipe Pose Landmarker
        print(f"Initializing MediaPipe Pose Landmarker ({model_version} model)...")
        
        try:
            # 获取模型文件路径
            model_path = self.get_model_path(model_version)
            
            # 创建基础选项（使用模型文件）
            base_options = python.BaseOptions(model_asset_path=model_path)
            
            # 创建姿态检测选项
            options = vision.PoseLandmarkerOptions(
                base_options=base_options,
                running_mode=vision.RunningMode.IMAGE,
                num_poses=1,
                min_pose_detection_confidence=0.5,
                min_pose_presence_confidence=0.5,
                min_tracking_confidence=0.5
            )
            
            self.detector = vision.PoseLandmarker.create_from_options(options)
            print(f"MediaPipe Pose initialized successfully with model: {model_path}")
        except Exception as e:
            print(f"Failed to initialize MediaPipe Pose: {e}")
            raise
        
        # 帧计数器（用于 VIDEO 模式的时间戳）
        self.frame_counter = 0
        
        # 加载运动配置用于角度点
        self.exercise_configs = self.load_exercise_configs()
    
    def get_model_path(self, model_version='lite'):
        """获取模型文件路径，支持lite/full/heavy版本"""
        model_filename = f'pose_landmarker_{model_version}.task'
        
        if getattr(sys, 'frozen', False):
            # 打包环境
            base_path = sys._MEIPASS
            model_path = os.path.join(base_path, 'models', model_filename)
        else:
            # 开发或Docker环境
            # 首先尝试Docker容器的绝对路径
            docker_path = f'/app/models/{model_filename}'
            if os.path.exists(docker_path):
                print(f"[PoseProcessor] 使用Docker模型路径: {docker_path}")
                return docker_path
            # 回退到相对路径用于本地开发
            model_path = os.path.join('models', model_filename)
        
        # 检查文件是否存在
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        return model_path
    
    def get_exercises_file_path(self):
        """获取 exercises.json 文件路径，兼容开发和打包环境"""
        if getattr(sys, 'frozen', False):
            # 打包环境
            # 首先检查 exe 旁边的外部 data 文件夹（用户可编辑）
            exe_dir = os.path.dirname(sys.executable)
            external_file = os.path.join(exe_dir, 'data', 'exercises.json')
            if os.path.exists(external_file):
                return external_file
            # 回退到 exe 内部打包的 data
            base_path = sys._MEIPASS
            exercises_file = os.path.join(base_path, 'data', 'exercises.json')
        else:
            # 开发或Docker环境
            # 首先尝试Docker容器的绝对路径
            docker_path = '/app/data/exercises.json'
            if os.path.exists(docker_path):
                print(f"[PoseProcessor] 使用Docker数据路径: {docker_path}")
                return docker_path
            # 回退到相对路径用于本地开发
            exercises_file = os.path.join('data', 'exercises.json')
        
        return exercises_file
    
    def load_exercise_configs(self):
        """从 JSON 文件加载运动配置"""
        exercises_file = self.get_exercises_file_path()
        
        try:
            if os.path.exists(exercises_file):
                with open(exercises_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    exercises = data.get('exercises', {})
                    
                    # 提取每个运动的 angle_point
                    configs = {}
                    for exercise_type, config in exercises.items():
                        configs[exercise_type] = {
                            'angle_point': config.get('angle_point', [])
                        }
                    
                    return configs
            else:
                print(f"错误：找不到运动配置文件 {exercises_file}")
                print("请确保 data/exercises.json 存在")
                return {}
        except Exception as e:
            print(f"加载运动配置时出错：{e}")
            return {}
    
    def process_frame(self, frame, exercise_type):
        """处理单帧进行姿态检测和运动计数"""
        import time
        start_time = time.time()
        # 大小检查，如果帧太大则调整大小
        h, w = frame.shape[:2]
        original_size = (w, h)
        
        # MediaPipe 适合中等分辨率，限制以提高性能
        if w > 640 or h > 640:
            scale = min(640/w, 640/h)
            frame = cv2.resize(frame, (int(w*scale), int(h*scale)))
            scale_factor = scale
        else:
            scale_factor = 1.0
        
        # 初始化结果
        current_angle = None
        angle_point = None
        keypoints = None
        
        try:
            # 转换为 RGB (MediaPipe 需要)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # 创建 MediaPipe Image 对象
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
            
            # 处理帧
            self.frame_counter += 1
            timestamp_ms = self.frame_counter * 33  # 假设 ~30 FPS
            
            # 使用 IMAGE 模式检测
            detect_start = time.time()
            detection_result = self.detector.detect(mp_image)
            detect_time = time.time() - detect_start
            
            # 提取关键点
            if detection_result.pose_landmarks:
                # 获取第一个人的关键点
                landmarks = detection_result.pose_landmarks[0]
                h, w = frame.shape[:2]
                
                # 转换为 numpy 数组 (33个关键点, x, y)
                keypoints = np.array([[lm.x * w, lm.y * h] for lm in landmarks])
                
                # 如果需要缩放回原始大小
                if scale_factor != 1.0:
                    keypoints = keypoints / scale_factor
                
                # 调用计数器进行计数（这会更新counter和stage）
                current_angle = self.exercise_counter.count_exercise(keypoints, exercise_type)
                
                # 根据运动类型获取对应的角度点用于可视化
                _, angle_point = self.get_exercise_angle(keypoints, exercise_type)
            
        except Exception as e:
            print(f"MediaPipe 处理失败：{e}")
        
        total_time = time.time() - start_time
        # 每60帧打印一次性能日志（降低日志频率）
        if self.frame_counter % 60 == 0:
            print(f"[性能] Frame #{self.frame_counter}: 总耗时 {total_time*1000:.1f}ms | 检测: {detect_time*1000:.1f}ms")
        
        # 返回处理后的帧、当前角度、角度点和关键点
        return None, current_angle, angle_point, keypoints
    
    def get_exercise_angle(self, keypoints, exercise_type):
        """根据运动类型获取角度"""
        current_angle = None
        angle_point = None
        
        try:
            # 根据运动类型获取计数方法
            count_method_map = {
                "squat": self.exercise_counter.count_squat,
                "pushup": self.exercise_counter.count_pushup,
                "situp": self.exercise_counter.count_situp,
                "bicep_curl": self.exercise_counter.count_bicep_curl,
                "lateral_raise": self.exercise_counter.count_lateral_raise,
                "overhead_press": self.exercise_counter.count_overhead_press,
                "leg_raise": self.exercise_counter.count_leg_raise,
                "knee_raise": self.exercise_counter.count_knee_raise,
                "knee_press": self.exercise_counter.count_knee_press,
                "crunch": self.exercise_counter.count_crunch
            }
            
            # 获取计数方法
            count_method = count_method_map.get(exercise_type)
            if count_method:
                current_angle = count_method(keypoints)
                
                # 从配置获取 angle_point
                if current_angle is not None and exercise_type in self.exercise_configs:
                    angle_point_indices = self.exercise_configs[exercise_type].get('angle_point', [])
                    if len(angle_point_indices) == 3:
                        angle_point = [
                            keypoints[angle_point_indices[0]],
                            keypoints[angle_point_indices[1]],
                            keypoints[angle_point_indices[2]]
                        ]
        except Exception as e:
            print(f"计算运动角度时出错：{e}")
            
        return current_angle, angle_point
    
    def set_skeleton_visibility(self, show):
        """设置骨骼显示状态"""
        self.show_skeleton = show
        print(f"骨骼显示：{'开' if show else '关'}")
    
    def __del__(self):
        """清理资源"""
        if hasattr(self, 'detector'):
            self.detector.close()
