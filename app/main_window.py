"""
主窗口类 - 负责基本的UI设置和信号连接
"""

import sys
import os
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                             QStatusBar, QMessageBox, QAction, QActionGroup, QMenu, QFileDialog)
from PyQt5.QtCore import Qt, QTimer

from core.video_thread import VideoThread
from core.pose_processor import PoseProcessor
from core.sound_manager import SoundManager
from core.settings_manager import SettingsManager
from core.workout_tracker import WorkoutTracker
from core.translations import Translations as T
from exercise_counters import ExerciseCounter
from ui.video_display import VideoDisplay
from ui.control_panel import ControlPanel
from ui.workout_stats_panel import WorkoutStatsPanel
from ui.styles import AppStyles

from .mode_manager import ModeManager
from .menu_manager import MenuManager
from .stats_manager import StatsManager
from .video_processor import VideoProcessor
from .counter_manager import CounterManager

class WorkoutTrackerApp(QMainWindow):
    """AI Fitness Assistant Main Window Class"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(T.get("app_title"))
        self.setMinimumSize(900, 900)
        
        # 初始化核心组件
        self._init_core_components()
        
        # 初始化管理器
        self._init_managers()
        
        # 创建UI
        self.setup_ui()
        
        # 初始化视频线程
        self.setup_video_thread()
        
        # 创建动画定时器
        self.setup_animation_timer()
        
        # 初始化面板
        self._init_panels()
        
        # 视频将在 MediaPipe 初始化后启动
        # self.start_video()  # 移到异步初始化方法中
        
        # 初始化状态变量
        self._init_state_variables()
        
        # 显示欢迎消息
        self.statusBar.showMessage(f"{T.get('welcome')} - 正在初始化...")
        
        # 异步初始化 MediaPipe（避免阻塞UI）
        QTimer.singleShot(100, self._init_mediapipe_async)
    
    def _init_core_components(self):
        """初始化核心组件"""
        # Initialize settings manager FIRST to load user preferences
        self.settings_manager = SettingsManager()
        print(f"[Settings] 已加载用户配置: {self.settings_manager.get_all()}")
        
        # 创建运动计数器
        self.exercise_counter = ExerciseCounter()
        
        # MediaPipe 姿态处理器将延迟初始化
        print("MediaPipe Pose 将在窗口显示后初始化...")
        self.pose_processor = None
        
        # 设置默认运动类型（从配置中读取）
        self.exercise_type = self.settings_manager.get('exercise_type', 'overhead_press')
        print(f"[Settings] 加载运动类型: {self.exercise_type}")
        
        # 创建声音管理器
        self.sound_manager = SoundManager()
        
        # 创建运动追踪器
        self.workout_tracker = WorkoutTracker()
        
        # 创建视频源管理器
        from app.video_source_manager import VideoSourceManager
        self.video_source_manager = VideoSourceManager()
        
        # TTS管理器
        self.init_tts_manager()
        
    
    def _init_managers(self):
        """初始化管理器"""
        # 模式管理器
        self.mode_manager = ModeManager(self)
        
        # 菜单管理器
        self.menu_manager = MenuManager(self)
        
        
        # 统计管理器
        self.stats_manager = StatsManager(self)
        
        # 视频处理器
        self.video_processor = VideoProcessor(self)
        
        # 计数器管理器
        self.counter_manager = CounterManager(self)
    
    def _init_panels(self):
        """初始化面板"""
        # 初始化运动统计面板
        self.stats_manager.init_workout_stats()
        
    
    def _init_state_variables(self):
        """初始化状态变量"""
        # 当前计数值
        self.current_count = 0
        
        # 手动计数追踪
        self.manual_count = 0
        
        # 重置操作标志
        self.is_resetting = False
        
        # 上次播报的计数值（防止重复播报）
        self.last_announced_count = -1
        
        # 默认不显示运动统计面板
        self.stats_panel.setVisible(False)
        
        # 镜像模式相关属性
        self.mirror_mode = True
    
    def _init_mediapipe_async(self):
        """异步初始化 MediaPipe（避免阻塞UI）"""
        try:
            print("Initializing MediaPipe Pose processor")
            self.statusBar.showMessage("正在初始化 MediaPipe...")
            
            # 初始化 MediaPipe 姿态处理器
            self.pose_processor = PoseProcessor(
                exercise_counter=self.exercise_counter
            )
            
            # 初始化完成，启动视频
            self.statusBar.showMessage(f"{T.get('welcome')} - MediaPipe Pose")
            print("MediaPipe 初始化完成，启动视频线程...")
            
            # 现在可以安全地启动视频处理
            self.start_video()
            
            # Restore UI state from saved settings
            QTimer.singleShot(500, self._restore_ui_from_settings)
            
        except Exception as e:
            print(f"MediaPipe 初始化失败: {e}")
            self.statusBar.showMessage(f"MediaPipe 初始化失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _restore_ui_from_settings(self):
        """Restore UI controls from saved settings"""
        try:
            print("[Settings] 正在恢复UI设置...")
            self.control_panel.restore_from_settings(self.settings_manager)
            print("[Settings] UI设置恢复完成")
        except Exception as e:
            print(f"[Settings] UI设置恢复失败: {e}")
            import traceback
            traceback.print_exc()
    
    def setup_ui(self):
        """设置用户界面"""
        # 窗口最大化
        self.showMaximized()
        
        # 应用样式
        self.setPalette(AppStyles.get_window_palette())
        self.setStyleSheet(AppStyles.get_global_stylesheet())
        
        # 创建主窗口布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # 创建左侧区域（视频和运动统计）
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加视频显示区域
        self.video_display = VideoDisplay()
        left_layout.addWidget(self.video_display)
        
        # 创建右侧区域（仅控制面板）
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加控制面板
        self.control_panel = ControlPanel()
        right_layout.addWidget(self.control_panel)
        
        # 不添加stretch，让ScrollArea填满整个右侧区域
        
        # 将左侧区域和右侧部件添加到主布局
        main_layout.addWidget(left_widget, 7)  # 为左侧区域分配70%空间
        main_layout.addWidget(right_widget, 3)  # 为右侧区域分配30%空间
        
        # 添加状态栏
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(T.get("ready"))
        
        # 设置菜单栏
        self.menu_manager.setup_menu_bar()
        
        # 连接控制面板信号
        self.connect_signals()
    
    def connect_signals(self):
        """连接信号和槽"""
        # 连接控制面板信号
        self.control_panel.exercise_changed.connect(self.change_exercise)
        self.control_panel.counter_reset.connect(self.reset_counter)

        self.control_panel.rotation_toggled.connect(self.toggle_rotation)
        self.control_panel.skeleton_toggled.connect(self.toggle_skeleton)
        self.control_panel.mirror_toggled.connect(self.toggle_mirror)
        
        # 连接新按钮信号
        self.control_panel.counter_increase.connect(self.increase_counter)
        self.control_panel.counter_decrease.connect(self.decrease_counter)
        self.control_panel.record_confirmed.connect(self.confirm_record)
        # 添加视频源信号连接
        self.control_panel.video_source_changed.connect(self.change_video_source)
        # 添加模型切换信号连接
        self.control_panel.model_changed.connect(self.change_model_version)
        # 添加TTS模式切换信号连接
        self.control_panel.tts_mode_changed.connect(self.change_tts_mode)
        
        # 连接统计面板信号
        if hasattr(self, 'stats_panel'):
            self.stats_panel.goal_updated.connect(self.update_goal)
            self.stats_panel.weekly_goal_updated.connect(self.update_weekly_goal)
            self.stats_panel.month_changed.connect(self.load_month_stats)
    
    def setup_video_thread(self):
        """设置视频处理线程"""
        # Get RTSP URL from settings
        rtsp_url = self.settings_manager.get('rtsp_url', 'rtsp://admin:ZYF001026@192.168.31.99:554/stream2')
        source_type = self.settings_manager.get('source_type', 'rtsp')
        
        print(f"[Settings] RTSP地址: {rtsp_url}")
        print(f"[Settings] 视频源类型: {source_type}")
        
        # 设置双分辨率：UI显示使用720p（平衡性能和质量），模型推理低分辨率
        # 降低分辨率以提升UI渲染性能，避免卡顿
        self.video_thread = VideoThread(
            camera_id=rtsp_url,  # 使用RTSP地址而不是摄像头ID
            rotate=False,  # RTSP摄像头通常不需要旋转
            display_width=1280,  # 降低到720p
            display_height=720,
            inference_width=640,
            inference_height=360
        )
        
        # 设置主窗口引用，用于存储推理帧
        self.video_thread.main_window = self
        
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        
        # 初始化FPS值和推理帧
        self.current_fps = 0
        self.current_inference_frame = None
    
    def setup_animation_timer(self):
        """设置动画定时器"""
        self.count_animation_timer = QTimer()
        self.count_animation_timer.setSingleShot(True)
        self.count_animation_timer.timeout.connect(self.control_panel.reset_counter_style)
    
    def start_video(self):
        """开始视频处理"""
        print("[主窗口] 调用 video_thread.start()...")
        try:
            self.video_thread.start()
            print("[主窗口] 视频线程已启动")
        except Exception as e:
            print(f"[错误] 视频线程启动失败: {e}")
            import traceback
            traceback.print_exc()
    
    def update_image(self, frame, fps=0):
        """更新图像显示并处理姿态检测"""
        self.video_processor.update_image(frame, fps)
    
    def change_exercise(self, exercise_type):
        """改变运动类型"""
        print(f"[主窗口] 更改运动类型: {exercise_type}")
        self.exercise_type = exercise_type
        
        # Save to settings
        self.settings_manager.set('exercise_type', exercise_type)
        
        # 通知计数管理器更新运动类型
        self.counter_manager.change_exercise(exercise_type)
    
    def reset_counter(self):
        """重置计数器"""
        self.counter_manager.reset_counter()
    
    def reset_exercise_state(self):
        """重置运动状态"""
        self.counter_manager.reset_exercise_state()
    
    def increase_counter(self, new_count):
        """手动增加计数器值"""
        self.counter_manager.increase_counter(new_count)
    
    def decrease_counter(self, new_count):
        """手动减少计数器值"""
        self.counter_manager.decrease_counter(new_count)
    
    def confirm_record(self, exercise_type):
        """确认记录当前计数结果到历史记录"""
        self.counter_manager.confirm_record(exercise_type)
    

    
    def toggle_rotation(self, rotate):
        """切换视频旋转模式"""
        self.video_processor.toggle_rotation(rotate)
    
    def toggle_skeleton(self, show):
        """切换骨架显示"""
        self.video_processor.toggle_skeleton(show)
    
    def toggle_mirror(self):
        """Toggle mirror mode"""
        self.video_processor.toggle_mirror()
        # Save mirror state
        if hasattr(self.video_processor, 'video_thread') and self.video_processor.video_thread:
            mirror_state = self.video_processor.video_thread.mirror
            self.settings_manager.set('mirror_mode', mirror_state)
    
    def change_video_source(self, source_type, source_input):
        """切换视频源"""
        try:
            print(f"[主窗口] 切换视频源: 类型={source_type}, 输入={source_input}")
            
            # 停止当前视频线程
            if hasattr(self, 'video_thread') and self.video_thread.isRunning():
                print("[主窗口] 停止当前视频线程...")
                self.video_thread.stop()
            
            # 根据类型设置camera_id
            if source_type == "camera":
                camera_id = int(source_input) if source_input.isdigit() else 0
            else:  # rtsp or http
                camera_id = source_input
            
            # 重新创建视频线程
            print(f"[主窗口] 创建新视频线程: camera_id={camera_id}")
            self.video_thread = VideoThread(
                camera_id=camera_id,
                rotate=(source_type == "camera"),  # 只有本地摄像头旋转
                display_width=1280,
                display_height=720,
                inference_width=640,
                inference_height=360
            )
            
            # 设置主窗口引用
            self.video_thread.main_window = self
            
            # 连接信号
            self.video_thread.change_pixmap_signal.connect(self.update_image)
            
            # 启动视频线程
            self.video_thread.start()
            
            # Save settings
            self.settings_manager.update({
                'source_type': source_type,
                'rtsp_url': source_input if source_type in ['rtsp', 'http'] else self.settings_manager.get('rtsp_url')
            })
            
            # 更新UI状态
            self.control_panel.update_source_status(True, f"{source_type}")
            print(f"[主窗口] 视频源切换成功")
            
        except Exception as e:
            print(f"[错误] 视频源切换失败: {e}")
            import traceback
            traceback.print_exc()
            self.control_panel.update_source_status(False, str(e))
    
    def change_model_version(self, model_version):
        """切换MediaPipe模型版本"""
        try:
            print(f"[主窗口] 切换模型版本: {model_version}")
            
            # 显示提示
            self.statusBar.showMessage(f"正在切换到{model_version}模型...")
            
            # 重新初始化PoseProcessor
            from core.pose_processor import PoseProcessor
            
            # 删除旧的处理器
            if hasattr(self, 'pose_processor') and self.pose_processor:
                del self.pose_processor
            
            # 创建新的处理器
            self.pose_processor = PoseProcessor(
                exercise_counter=self.exercise_counter,
                model_version=model_version
            )
            
            print(f"[主窗口] 模型切换成功: {model_version}")
            self.statusBar.showMessage(f"已切换到{model_version}模型")
            
        except Exception as e:
            print(f"[错误] 模型切换失败: {e}")
            import traceback
            traceback.print_exc()
            self.statusBar.showMessage(f"模型切换失败: {e}")
    
    def init_tts_manager(self):
        """初始化TTS管理器"""
        import json
        from core.ha_api_manager import HAAPIManager
        
        # 加载TTS配置
        config_path = 'data/tts_config.json'
        self.tts_config = {}
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.tts_config = json.load(f)
        except:
            # 使用默认配置
            self.tts_config = {
                'mode': 'sound',
                'ha_config': {
                    'base_url': '',
                    'token': '',
                    'service_path': '',
                    'body_params': []
                }
            }
        
        # 创建HA API管理器
        ha_config = self.tts_config.get('ha_config', {})
        self.ha_api = HAAPIManager(
            ha_config.get('base_url', ''),
            ha_config.get('token', '')
        )
        print(f"[TTS] 初始化完成，模式: {self.tts_config.get('mode', 'sound')}")
    
    def change_tts_mode(self, mode):
        """切换TTS模式"""
        self.tts_config['mode'] = mode
        # Save to settings
        self.settings_manager.set('tts_mode', mode)
        print(f"[TTS] 切换模式: {mode}")
        
        # 重新加载HA配置
        if mode == 'ha':
            import json
            try:
                with open('data/tts_config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    ha_config = config.get('ha_config', {})
                    self.ha_api.update_config(
                        ha_config.get('base_url', ''),
                        ha_config.get('token', '')
                    )
            except Exception as e:
                print(f"[错误] 加载HA配置失败: {e}")
    
    def announce_count(self, count, exercise_name):
        """播报计数"""
        # 防止重复播报
        if count == getattr(self, 'last_announced_count', -1):
            return
        self.last_announced_count = count
        
        mode = self.tts_config.get('mode', 'sound')
        print(f"[TTS-Debug] announce_count被调用: count={count}, exercise={exercise_name}, mode={mode}", flush=True)
        
        if mode == 'sound':
            # 播放音效
            print("[TTS-Debug] 调用 play_success_sound()", flush=True)
            self.play_success_sound(count)
        elif mode == 'ha':
            # 调用HA API
            self.announce_via_ha(count, exercise_name)
    
    def announce_via_ha(self, count, exercise_name):
        """通过HA播报"""
        try:
            import json
            # 重新加载配置确保最新
            with open('data/tts_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            ha_config = config.get('ha_config', {})
            
            # 准备变量
            # 尝试从stats面板获取目标次数
            total_goal = 0
            if hasattr(self, 'stats_panel') and hasattr(self.stats_panel, 'goal_manager'):
                total_goal = self.stats_panel.goal_manager.get_goal(exercise_name) or 0
            
            variables = {
                'count': count,
                'exercise': exercise_name,
                'total': total_goal
            }
            
            # 准备请求体
            body = self.ha_api.prepare_body_with_variables(
                ha_config.get('body_params', []),
                variables
            )
            
            # 调用服务
            success, message = self.ha_api.call_service(
                ha_config.get('service_path', ''),
                body
            )
            
            if success:
                print(f"[TTS] HA播报成功: 第{count}次{exercise_name}")
            else:
                print(f"[TTS] HA播报失败: {message}")
                # 失败时回退到音效
                self.play_success_sound(count)
                
        except Exception as e:
            print(f"[错误] HA播报异常: {e}")
            import traceback
            traceback.print_exc()
            # 异常时回退到音效
            self.play_success_sound(count)
    
    def play_success_sound(self, count=None):
        """播放成功音效"""
        # 调用SoundManager播放计数音效
        if hasattr(self, 'sound_manager') and self.sound_manager:
            # Check if it's a milestone (every 10 counts)
            if count and count % 10 == 0:
                print(f"[主窗口] 里程碑检测: 第{count}次，播放特殊音效", flush=True)
                self.sound_manager.play_milestone_sound(count)
            else:
                self.sound_manager.play_count_sound(count)
    
    def open_video_file(self):
        """打开视频文件"""
        self.video_processor.open_video_file()
    

    
    def switch_to_camera_mode(self):
        """切换回摄像头模式"""
        self.video_processor.switch_to_camera_mode()

    def switch_to_workout_mode(self):
        """切换到运动模式"""
        self.mode_manager.switch_to_workout_mode()
    
    def switch_to_stats_mode(self):
        """切换到统计管理模式"""
        self.mode_manager.switch_to_stats_mode()
    
    def switch_to_voice_control_mode(self):
        """切换到语音控制模式"""
        self.mode_manager.switch_to_voice_control_mode()
    
    def show_about(self):
        """显示关于对话框"""
        self.menu_manager.show_about()
    
    def change_language(self, language):
        """更改界面语言"""
        self.menu_manager.change_language(language)
    
    def update_today_stats(self):
        """更新今日运动统计"""
        self.stats_manager.update_today_stats()
    
    def update_stats_overview(self):
        """更新所有统计概览"""
        self.stats_manager.update_stats_overview()
    
    def load_month_stats(self, year, month):
        """加载指定月份的统计数据"""
        self.stats_manager.load_month_stats(year, month)
    
    def update_goal(self, exercise_type, count):
        """更新运动目标"""
        self.stats_manager.update_goal(exercise_type, count)
    
    def update_weekly_goal(self, count):
        """更新周目标"""
        self.stats_manager.update_weekly_goal(count)
    
    def closeEvent(self, event):
        """关闭窗口时清理资源"""
        if self.video_thread.isRunning():
            self.video_thread.stop()
        
        
        event.accept() 