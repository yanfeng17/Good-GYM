import cv2
import numpy as np
import time
import os
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class VideoThread(QThread):
    """Video stream processing thread to avoid UI freezing"""
    change_pixmap_signal = pyqtSignal(np.ndarray, float)  # Add FPS parameter
    
    def __init__(self, camera_id=0, rotate=True, display_width=1280, display_height=720, inference_width=640, inference_height=360):
        super().__init__()
        self.camera_id = camera_id
        self.rotate = rotate
        self._run_flag = True
        self.buffer_size = 1  # Buffer size, set to 1 to avoid delay
        self.video_file = None  # Local video file path
        self.is_camera = True  # Whether to use camera
        self.fps = 30  # Default frame rate
        self.loop_video = False  # Control whether to loop video playback
        self.video_ended = False  # Mark if video has ended
        self.mirror = True  # Default mirror mode on (matches UI switch default)
        self.display_width = display_width
        self.display_height = display_height
        self.inference_width = inference_width
        self.inference_height = inference_height

    def set_camera(self, camera_id):
        """Switch camera"""
        if self.isRunning():
            self._run_flag = False
            self.wait()
        self.camera_id = camera_id
        self.video_file = None  # Clear video file path
        self.is_camera = True  # Switch back to camera mode
        self._run_flag = True
        self.start()
    
    def set_rotation(self, rotate):
        """Set whether to rotate video"""
        self.rotate = rotate
        
    def set_mirror(self, mirror):
        """Set whether to mirror video"""
        self.mirror = mirror
        
    def set_video_file(self, file_path, loop=False):
        """Set video file path
        
        Args:
            file_path (str): Video file path
            loop (bool): Whether to loop video playback, default is False
        """
        if self.isRunning():
            self._run_flag = False
            self.wait()
        self.video_file = file_path
        self.is_camera = False  # Switch to video file mode
        self.loop_video = loop  # Set whether to loop playback
        self.video_ended = False  # Reset video end flag
        
        # Pre-detect video aspect ratio to decide which rotation mode to apply
        self.auto_detect_orientation(file_path)
        
        self._run_flag = True
        self.start()
        
    def auto_detect_orientation(self, file_path):
        """Automatically detect video file aspect ratio and set appropriate rotation mode"""
        try:
            if not os.path.exists(file_path):
                print(f"Error: Video file does not exist {file_path}")
                return
                
            temp_cap = cv2.VideoCapture(file_path)
            if not temp_cap.isOpened():
                print(f"Error: Cannot open video file for aspect ratio detection {file_path}")
                return
                
            # Get original video size information (not dependent on frame reading)
            original_width = int(temp_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            original_height = int(temp_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # If first frame can be obtained, use first frame size information to confirm
            ret, first_frame = temp_cap.read()
            if ret:
                height, width = first_frame.shape[:2]
                # Check if frame size matches video size
                if height != original_height or width != original_width:
                    # If there's a difference, use frame size
                    original_width = width
                    original_height = height
                    print("Frame size differs from video size, using frame size information")
            
            # Release temporary camera
            temp_cap.release()
            
            # Calculate aspect ratio
            aspect_ratio = original_width / original_height
            
            # Determine video orientation
            # Vertical ratio less than 0.8, horizontal ratio greater than 1.3, middle value is square
            is_vertical = aspect_ratio < 0.8
            
            # If it's a vertical video (9:16)
            if is_vertical:
                print(f"Detected vertical video (aspect ratio: {aspect_ratio:.2f}, size: {original_width}x{original_height})")
                self.rotate = False  # No rotation
                # Set display resolution
                self.display_width = max(720, original_width)
                self.display_height = int(self.display_width * original_height / original_width)
                # Set inference resolution
                self.inference_width = max(360, original_width)
                self.inference_height = int(self.inference_width * original_height / original_width)
            # Otherwise it's a horizontal video (16:9)
            else:
                print(f"Detected horizontal video (aspect ratio: {aspect_ratio:.2f}, size: {original_width}x{original_height})")
                self.rotate = False  # Also no rotation
                # Set display resolution
                self.display_height = 720
                self.display_width = int(self.display_height * aspect_ratio)
                # Set inference resolution
                self.inference_height = 480
                self.inference_width = int(self.inference_height * aspect_ratio)
        except Exception as e:
            print(f"Video aspect ratio detection error: {str(e)}")
            # Use default values when error occurs
            self.rotate = False
    
    def run(self):
        """Main thread loop"""
        # 判断摄像头类型
        if isinstance(self.camera_id, str):
            if self.camera_id.lower().startswith('rtsp://'):
                camera_type = "RTSP摄像头"
            elif self.camera_id.lower().startswith('http://') or self.camera_id.lower().startswith('https://'):
                camera_type = "HTTP/IP摄像头"
            else:
                camera_type = f"网络摄像头({self.camera_id})"
        else:
            camera_type = f"本地摄像头{self.camera_id}"
        
        print(f"[视频线程] 开始运行，模式: {camera_type if self.is_camera else '文件'}")
        
        # Open video source based on mode (camera or file)
        if self.is_camera:
            print(f"[视频线程] 正在打开 {camera_type}...")
            print(f"[视频线程] 地址: {self.camera_id}")
            
            # OpenCV支持RTSP URL和摄像头ID  
            # 对于RTSP，使用FFmpeg后端并设置参数
            if isinstance(self.camera_id, str):
                url_lower = self.camera_id.lower()
                
                if url_lower.startswith('rtsp://'):
                    print("[视频线程] 使用RTSP协议，配置FFmpeg后端...")
                    
                    # 设置OpenCV使用TCP而不是UDP（更稳定但延迟略高）
                    os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|buffer_size;1024000'
                    
                    # 强制使用FFmpeg后端处理RTSP流
                    self.cap = cv2.VideoCapture(self.camera_id)
                    
                    if self.cap.isOpened():
                        print("[视频线程] RTSP连接成功！")
                    else:
                        print("[视频线程] 尝试使用备用参数重新连接...")
                        self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_ANY)
                    
                    # RTSP优化设置
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 最小化延迟
                    self.cap.set(cv2.CAP_PROP_FPS, 30)  # 尝试设置更高帧率
                    
                elif url_lower.startswith('http://') or url_lower.startswith('https://'):
                    print("[视频线程] 使用HTTP协议，打开IP摄像头...")
                    
                    # HTTP流直接打开，不需要特殊配置
                    self.cap = cv2.VideoCapture(self.camera_id)
                    
                    if self.cap.isOpened():
                        print("[视频线程] HTTP连接成功！")
                    else:
                        print("[视频线程] HTTP连接失败，尝试其他方式...")
                        self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_FFMPEG)
                    
                    # HTTP优化设置 - 减少缓冲降低延迟
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 最小缓冲减少延迟
                    print("[视频线程] HTTP缓冲已设置为最小值以减少延迟")
                else:
                    # 其他URL格式
                    print(f"[视频线程] 打开网络流: {self.camera_id}")
                    self.cap = cv2.VideoCapture(self.camera_id)
            else:
                self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                print(f"[错误] 无法打开摄像头")
                if isinstance(self.camera_id, str):
                    url_lower = self.camera_id.lower()
                    if url_lower.startswith('rtsp://'):
                        print(f"[提示] RTSP连接失败，请检查：")
                        print(f"  1) 网络连接是否正常")
                        print(f"  2) RTSP地址是否正确")
                        print(f"  3) 用户名密码是否正确")
                        print(f"  4) 摄像头是否在线")
                    elif url_lower.startswith('http://') or url_lower.startswith('https://'):
                        print(f"[提示] HTTP连接失败，请检查：")
                        print(f"  1) URL格式: http://IP:端口/路径")
                        print(f"  2) 网络连接是否正常")
                        print(f"  3) IP摄像头应用是否运行")
                        print(f"  4) 端口是否正确(IP Webcam通常是8080)")
                    else:
                        print(f"[提示] 网络流连接失败，检查URL格式和网络")
                else:
                    print(f"[提示] 请检查：1) 摄像头是否被其他程序占用 2) 摄像头权限 3) 摄像头是否正常工作")
                return
            
            print(f"[视频线程] 摄像头打开成功，正在设置参数...")
            
            # Set camera parameters (对RTSP可能无效，但不会出错)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.display_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.display_height)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.buffer_size)
            
            # RTSP摄像头通常不需要旋转
            if not isinstance(self.camera_id, str):
                # Camera mode defaults to rotation (default to portrait mode)
                self.rotate = True
            
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"[视频线程] 摄像头已就绪: 分辨率={actual_width}x{actual_height}")
        else:
            # Open video file
            if not os.path.exists(self.video_file):
                print(f"Error: Video file does not exist {self.video_file}")
                return
                
            self.cap = cv2.VideoCapture(self.video_file)
            if not self.cap.isOpened():
                print(f"Error: Cannot open video file {self.video_file}")
                return
                
            video_name = os.path.basename(self.video_file)
            print(f"Video file opened: {video_name}, resolution={int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
            
            # Get actual frame rate (may differ from requested)
            real_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
            if real_fps == 0:
                real_fps = 30  # Default value
            
            # Limit maximum frame rate to 30fps
            self.fps = min(real_fps, 30)
            print(f"Frame rate: original {real_fps}fps, current display {self.fps}fps")
        
        # Initialize FPS calculation with moving average
        frame_count = 0
        fps_history = []
        fps_window = 30  # 使用30帧的移动平均
        fps_display = 0
        last_fps_time = time.time()
        
        # Run flag
        while self._run_flag:
            ret, frame = self.cap.read()
            if ret:
                # 创建两个版本的帧：高分辨率用于显示，低分辨率用于推理
                display_frame = frame.copy()
                inference_frame = cv2.resize(frame, (self.inference_width, self.inference_height))
                
                # 对显示帧应用旋转（如果需要）
                if self.rotate:
                    display_frame = cv2.rotate(display_frame, cv2.ROTATE_90_CLOCKWISE)
                    # 同时旋转推理帧
                    inference_frame = cv2.rotate(inference_frame, cv2.ROTATE_90_CLOCKWISE)
                
                # 注意：镜像处理已移至 video_processor.py 中进行
                # 这里不再应用镜像，避免重复镜像导致效果抵消
                
                # 将推理帧存储在主窗口中，供模型使用
                if hasattr(self.main_window, 'current_inference_frame'):
                    self.main_window.current_inference_frame = inference_frame
                
                # Calculate FPS using moving average for stability
                frame_count += 1
                current_time = time.time()
                
                # 计算当前帧的FPS
                if frame_count > 1:
                    time_delta = current_time - last_fps_time
                    if time_delta > 0:  # 避免除零错误
                        frame_fps = 1.0 / time_delta
                        fps_history.append(frame_fps)
                        
                        # 保持窗口大小
                        if len(fps_history) > fps_window:
                            fps_history.pop(0)
                        
                        # 使用移动平均得到稳定的FPS
                        if len(fps_history) > 0:
                            fps_display = sum(fps_history) / len(fps_history)
                
                last_fps_time = current_time
                
                # Send display frame and FPS information
                # 日志已禁用以提升UI性能
                self.change_pixmap_signal.emit(display_frame, fps_display)
            else:
                # When reading video file fails, if in video file mode
                if not self.is_camera and self.video_file:
                    # Check if loop playback is needed
                    if self.loop_video:
                        # Loop mode: reset to beginning and continue playback
                        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = self.cap.read()
                        if ret:
                            # Send frame and FPS information
                            self.change_pixmap_signal.emit(frame, fps_display)
                        else:
                            # If reset still cannot read, output warning
                            print("Warning: Video file playback ended and cannot loop again")
                            self.video_ended = True
                    else:
                        # Non-loop mode: mark video as ended
                        if not self.video_ended:
                            print("Video playback completed, stopped at last frame")
                            self.video_ended = True
                else:
                    print("Warning: Cannot read video frame")
            
            # RTSP流不需要sleep限制帧率，否则会造成卡顿
            # 只对本地视频文件限制帧率
            if not self.is_camera:
                time.sleep(1/self.fps)
        
        # Release resources
        self.cap.release()
    
    def stop(self):
        """Stop thread"""
        self._run_flag = False
        self.wait()
