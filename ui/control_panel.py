from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QComboBox, QGroupBox, QFrame, QLineEdit, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
import json
import os
import sys
from .styles import AppStyles
from .custom_widgets import SwitchControl
from core.translations import Translations as T

class ControlPanel(QWidget):
    """Control panel component"""
    
    # Define signals
    exercise_changed = pyqtSignal(str)
    counter_reset = pyqtSignal()
    rotation_toggled = pyqtSignal(bool)
    skeleton_toggled = pyqtSignal(bool)
    counter_increase = pyqtSignal(int)
    counter_decrease = pyqtSignal(int)
    record_confirmed = pyqtSignal(str)
    mirror_toggled = pyqtSignal(bool)
    video_source_changed = pyqtSignal(str, str)  # type, url/id
    model_changed = pyqtSignal(str)  # lite/full/heavy
    tts_mode_changed = pyqtSignal(str)  # sound/ha
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.exercise_colors = AppStyles.EXERCISE_COLORS
        
        # Initialize exercise type mappings from JSON file
        self.exercise_display_map = self.load_exercise_display_map()
        
        # Initialize model type mappings - only keep RTMPose options
        self.model_display_map = {
            "lightweight": T.get("lightweight"),
            "balanced": T.get("balanced"),
            "performance": T.get("performance")
        }
        
        # Initialize reverse mappings
        self.exercise_code_map = {v: k for k, v in self.exercise_display_map.items()}
        self.current_exercise = "overhead_press"
        
        # Setup layout
        self.layout = QVBoxLayout(self)
        self.setup_ui()
    
    def get_exercises_file_path(self):
        """Get exercises.json file path, compatible with development and packaged environments"""
        if getattr(sys, 'frozen', False):
            # Packaged environment
            # First check for external data folder next to exe (user editable)
            exe_dir = os.path.dirname(sys.executable)
            external_file = os.path.join(exe_dir, 'data', 'exercises.json')
            if os.path.exists(external_file):
                return external_file
            # Fall back to bundled data inside exe
            base_path = sys._MEIPASS
            exercises_file = os.path.join(base_path, 'data', 'exercises.json')
        else:
            # Development or Docker environment
            # First try absolute path for Docker container
            docker_path = '/app/data/exercises.json'
            if os.path.exists(docker_path):
                print(f"[控制面板] 使用Docker路径: {docker_path}")
                return docker_path
            # Fall back to relative path for local development
            exercises_file = os.path.join('data', 'exercises.json')
        
        return exercises_file
    
    def load_exercise_display_map(self):
        """Load exercise display map from JSON file"""
        exercises_file = self.get_exercises_file_path()
        
        # Debug log
        print(f"[控制面板] 尝试加载运动类型文件: {exercises_file}")
        print(f"[控制面板] 文件存在: {os.path.exists(exercises_file)}")
        
        try:
            if os.path.exists(exercises_file):
                with open(exercises_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    exercises = data.get('exercises', {})
                    
                    # Build exercise_display_map from JSON file
                    exercise_map = {}
                    current_lang = T.get_language()  # Get current language setting
                    
                    for exercise_type, config in exercises.items():
                        # Get display name from JSON file based on current language
                        if current_lang == 'zh':
                            display_name = config.get('name_zh', '')
                        elif current_lang == 'en':
                            display_name = config.get('name_en', '')
                        else:
                            # Fallback to English if language not supported
                            display_name = config.get('name_en', '')
                        
                        # If name not found in JSON, try translation module as fallback
                        if not display_name:
                            display_name = T.get(exercise_type)
                        
                        if display_name:
                            exercise_map[exercise_type] = display_name
                    
                    if exercise_map:
                        print(f"[控制面板] 成功加载 {len(exercise_map)} 种运动: {list(exercise_map.keys())}")
                        return exercise_map
                    else:
                        print(f"WARNING: No exercises found in {exercises_file}, using defaults")
                        return self._get_default_exercises()
            else:
                print(f"ERROR: Exercises file not found at {exercises_file}")
                print("Using default exercises instead")
                return self._get_default_exercises()
        except Exception as e:
            print(f"ERROR loading exercises from JSON: {e}")
            import traceback
            traceback.print_exc()
            print("Using default exercises instead")
            return self._get_default_exercises()
    
    def _get_default_exercises(self):
        """Return default exercise types when JSON loading fails - matches exercises.json"""
        return {
            "squat": "深蹲",
            "pushup": "俯卧撑",
            "situp": "仰卧起坐",
            "bicep_curl": "弯举",
            "lateral_raise": "侧平举",
            "overhead_press": "推举",
            "leg_raise": "抬腿",
            "knee_raise": "抬膝",
            "knee_press": "压膝",
            "crunch": "卷腹"
        }
    
    def setup_ui(self):
        """Setup control panel UI"""
        # Create Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        # Create content widget to hold everything
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setSpacing(15)  # Add some spacing between groups
        
        # Application title
        self.title_label = QLabel(T.get("app_title"))
        self.title_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("font-size: 25pt; font-weight: bold; color: #2c3e50; margin-bottom: 5px;")
        self.content_layout.addWidget(self.title_label)
        
        # Add info group
        self.setup_info_group()
        
        # Add control options group
        self.setup_controls_group()
        
        # Add phase display group
        self.setup_phase_group()
        
        # Add stretch at the bottom
        self.content_layout.addStretch()
        
        # Set content widget to scroll area
        scroll.setWidget(content_widget)
        
        # Add scroll area to main layout
        self.layout.addWidget(scroll)
    
    def setup_info_group(self):
        """Setup exercise info group"""
        self.info_group = QGroupBox(T.get("exercise_data"))
        self.info_group.setStyleSheet(AppStyles.get_group_box_style())
        info_layout = QVBoxLayout(self.info_group)
        
        # Create counter display
        counter_layout = QHBoxLayout()
        self.counter_label = QLabel(T.get("count_completed"))
        self.counter_label.setStyleSheet("color: #2c3e50; font-size: 20pt; font-weight: bold;")
        self.counter_label.setMinimumHeight(40)
        
        self.counter_value = QLabel("0")
        self.counter_value.setStyleSheet(AppStyles.get_counter_value_style())
        self.counter_value.setAlignment(Qt.AlignCenter)
        self.counter_value.setFixedSize(180, 120)
        
        counter_layout.addWidget(self.counter_label)
        counter_layout.addWidget(self.counter_value, 1, Qt.AlignCenter)
        info_layout.addLayout(counter_layout)
        
        # Add spacing
        spacer = QWidget()
        spacer.setMinimumHeight(10)
        info_layout.addWidget(spacer)
        
        # Angle display - comment out this code section
        # angle_layout = QHBoxLayout()
        # self.angle_label = QLabel(T.get("current_angle"))
        # self.angle_label.setStyleSheet("color: #2c3e50; font-size: 20pt; font-weight: bold;")
        # self.angle_label.setMinimumHeight(40)
        # 
        # self.angle_value = QLabel("0°")
        # self.angle_value.setStyleSheet(AppStyles.get_angle_value_style())
        # self.angle_value.setAlignment(Qt.AlignCenter)
        # self.angle_value.setFixedSize(180, 70)
        # 
        # angle_layout.addWidget(self.angle_label)
        # angle_layout.addWidget(self.angle_value, 1, Qt.AlignCenter)
        # info_layout.addLayout(angle_layout)
        
        self.content_layout.addWidget(self.info_group)
    
    def setup_controls_group(self):
        """Setup control options group"""
        self.controls_group = QGroupBox(T.get("control_options"))
        self.controls_group.setStyleSheet(AppStyles.get_group_box_style())
        controls_layout = QVBoxLayout(self.controls_group)
        controls_layout.setSpacing(8)  # Reduce overall layout spacing
        controls_layout.setContentsMargins(8, 15, 8, 8)  # Reduce margins
        
        # Exercise type selection
        self.exercise_label = QLabel(T.get("exercise_type"))
        self.exercise_label.setStyleSheet("color: #2c3e50; font-size: 10pt; font-weight: bold;")
        controls_layout.addWidget(self.exercise_label)
        
        self.exercise_combo = QComboBox()
        # Set dropdown menu style
        self.exercise_combo.setStyleSheet(AppStyles.get_exercise_combo_style())
        
        # Use our predefined exercise type mappings
        for code, display in self.exercise_display_map.items():
            self.exercise_combo.addItem(display)
        
        # Set default selected item
        overhead_press_text = self.exercise_display_map.get("overhead_press", "")
        if overhead_press_text:
            self.exercise_combo.setCurrentText(overhead_press_text)
            
        self.exercise_combo.currentTextChanged.connect(self._on_exercise_changed)
        controls_layout.addWidget(self.exercise_combo)
        
        # Video Source selection
        video_source_layout = QVBoxLayout()
        
        # Title
        source_title = QLabel(T.get("video_source"))
        source_title.setStyleSheet("color: #2c3e50; font-size: 10pt; font-weight: bold;")
        video_source_layout.addWidget(source_title)
        
        # Source type selector
        video_source_layout.addWidget(QLabel("类型:"))
        self.source_type_combo = QComboBox()
        self.source_type_combo.setStyleSheet(AppStyles.get_exercise_combo_style())
        self.source_type_combo.addItem("RTSP摄像头", "rtsp")
        self.source_type_combo.addItem("IP摄像头(HTTP)", "http")
        video_source_layout.addWidget(self.source_type_combo)
        
        # URL/ID input
        video_source_layout.addWidget(QLabel("地址:"))
        self.source_url_input = QLineEdit()
        self.source_url_input.setPlaceholderText("输入RTSP或HTTP地址...")
        self.source_url_input.setStyleSheet("""
            QLineEdit {
                padding: 4px;
                border: 2px solid #bdc3c7;
                border-radius: 4px;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        video_source_layout.addWidget(self.source_url_input)
        
        # Connect button
        button_layout = QHBoxLayout()
        self.connect_source_btn = QPushButton("连接")
        self.connect_source_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.connect_source_btn.clicked.connect(self._on_connect_source)
        
        self.source_status_label = QLabel("● 未连接")
        self.source_status_label.setStyleSheet("color: #7f8c8d; font-size: 9pt;")
        
        button_layout.addWidget(self.connect_source_btn)
        button_layout.addWidget(self.source_status_label)
        button_layout.addStretch()
        video_source_layout.addLayout(button_layout)
        
        controls_layout.addLayout(video_source_layout)
        controls_layout.addWidget(self._create_separator())
        
        # Model Version Selection
        model_layout = QVBoxLayout()
        
        model_title = QLabel("模型版本:")
        model_title.setStyleSheet("color: #2c3e50; font-size: 10pt; font-weight: bold;")
        model_layout.addWidget(model_title)
        
        model_select_layout = QVBoxLayout()
        model_select_layout.addWidget(QLabel("精度:"))
        self.model_combo = QComboBox()
        self.model_combo.setStyleSheet(AppStyles.get_exercise_combo_style())
        self.model_combo.addItem("Lite - 快速（推荐）", "lite")
        self.model_combo.addItem("Full - 平衡", "full")
        self.model_combo.addItem("Heavy - 精确（慢）", "heavy")
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)
        model_select_layout.addWidget(self.model_combo)
        model_layout.addLayout(model_select_layout)
        
        controls_layout.addLayout(model_layout)
        controls_layout.addWidget(self._create_separator())
        
        # TTS Voice Announcement
        tts_layout = QVBoxLayout()
        
        tts_title = QLabel("语音播报:")
        tts_title.setStyleSheet("color: #2c3e50; font-size: 10pt; font-weight: bold;")
        tts_layout.addWidget(tts_title)
        
        mode_layout = QVBoxLayout()
        mode_layout.addWidget(QLabel("模式:"))
        self.tts_mode_combo = QComboBox()
        self.tts_mode_combo.setStyleSheet(AppStyles.get_exercise_combo_style())
        self.tts_mode_combo.addItem("🔊 本地音效", "sound")
        self.tts_mode_combo.addItem("🏠 Home Assistant", "ha")
        self.tts_mode_combo.currentIndexChanged.connect(self._on_tts_mode_changed)
        mode_layout.addWidget(self.tts_mode_combo)
        tts_layout.addLayout(mode_layout)
        
        # HA配置按钮
        ha_btn_layout = QHBoxLayout()
        self.ha_config_btn = QPushButton("⚙ 配置Home Assistant")
        self.ha_config_btn.clicked.connect(self._open_ha_config)
        self.ha_config_btn.setEnabled(False)  # 默认禁用
        ha_btn_layout.addWidget(self.ha_config_btn)
        tts_layout.addLayout(ha_btn_layout)
        
        controls_layout.addLayout(tts_layout)
        controls_layout.addWidget(self._create_separator())

        
        # Skeleton display toggle
        self.skeleton_switch = SwitchControl(T.get("skeleton_display"))
        self.skeleton_switch.switched.connect(self._on_skeleton_toggled)
        controls_layout.addWidget(self.skeleton_switch)
        
        # Mirror mode toggle
        self.mirror_switch = SwitchControl(T.get("mirror_mode"))
        self.mirror_switch.switched.connect(self._on_mirror_toggled)
        controls_layout.addWidget(self.mirror_switch)
        
        # Add spacing
        spacer = QWidget()
        spacer.setMinimumHeight(5)
        controls_layout.addWidget(spacer)
        
        # Counter operation button row
        counter_buttons_layout = QHBoxLayout()
        # Decrease count button - orange-red
        self.decrease_button = QPushButton(T.get("decrease"))
        self.decrease_button.setFixedSize(80, 32)
        self.decrease_button.setStyleSheet(AppStyles.get_decrease_button_style())
        self.decrease_button.clicked.connect(self._on_decrease_counter)
        counter_buttons_layout.addWidget(self.decrease_button)

        # Increase count button - green
        self.increase_button = QPushButton(T.get("increase"))
        self.increase_button.setFixedSize(80, 32)
        self.increase_button.setStyleSheet(AppStyles.get_increase_button_style())
        self.increase_button.clicked.connect(self._on_increase_counter)
        counter_buttons_layout.addWidget(self.increase_button)
        
        # Reset counter button - gray
        self.reset_button = QPushButton(T.get("reset"))
        self.reset_button.setFixedSize(80, 32)
        self.reset_button.setStyleSheet(AppStyles.get_reset_button_style())
        self.reset_button.clicked.connect(self._on_reset_counter)
        counter_buttons_layout.addWidget(self.reset_button)

        # Confirm record button - blue system
        self.confirm_button = QPushButton(T.get("confirm"))
        self.confirm_button.setFixedSize(80, 32)
        self.confirm_button.setStyleSheet(AppStyles.get_confirm_button_style())
        self.confirm_button.clicked.connect(self._on_confirm_record)
        counter_buttons_layout.addWidget(self.confirm_button)

        controls_layout.addLayout(counter_buttons_layout)
        
        self.content_layout.addWidget(self.controls_group)
    
    def _on_increase_counter(self):
        """Manually increase counter value"""
        try:
            # Get current count value
            current_count = int(self.counter_value.text())
            
            # Increase by 1 each time
            new_count = current_count + 1
            
            # Update display
            self.counter_value.setText(str(new_count))
            
            # Send signal
            self.counter_increase.emit(new_count)
            
            # Show success animation
            self.show_success_animation()
            
        except ValueError:
            # If count value is not a valid number, reset to 1
            self.counter_value.setText("1")
            self.counter_increase.emit(1)

    def _on_decrease_counter(self):
        """Manually decrease counter value"""
        try:
            # Get current count value
            current_count = int(self.counter_value.text())
            
            # Ensure count doesn't go negative
            new_count = max(0, current_count - 1)
            
            # Update display
            self.counter_value.setText(str(new_count))
            
            # Send signal
            self.counter_decrease.emit(new_count)
            
            # Update style
            self.update_counter_style()
            
        except ValueError:
            # If count value is not a valid number, reset to 0
            self.counter_value.setText("0")
            self.counter_decrease.emit(0)

    def _on_confirm_record(self):
        """Confirm record current exercise result"""
        try:
            # Get current count value
            current_count = int(self.counter_value.text())
            
            # Only record if count is greater than 0
            if current_count > 0:
                # Send confirm record signal with current exercise type
                self.record_confirmed.emit(self.current_exercise)
                
                # Show success style - change background to green
                self.confirm_button.setStyleSheet(
                    AppStyles.get_success_button_style()
                )
                
                # Return to normal style after 1.5 seconds
                QTimer.singleShot(1500, lambda: self.confirm_button.setStyleSheet(
                    AppStyles.get_confirm_button_style()
                ))
                
        except ValueError:
            # If count value is not a valid number, ignore directly
            pass
    
    def setup_phase_group(self):
        """Setup phase display group"""
        self.phase_group = QGroupBox(T.get("phase_display"))
        self.phase_group.setStyleSheet(AppStyles.get_group_box_style())
        phase_layout = QVBoxLayout(self.phase_group)
        
        # Current phase label
        phase_label_layout = QHBoxLayout()
        self.phase_title = QLabel(T.get("current_phase"))
        self.phase_title.setStyleSheet("color: #2c3e50; font-size: 20pt; font-weight: bold;")
        
        phase_label_layout.addWidget(self.phase_title)
        phase_layout.addLayout(phase_label_layout)
        
        # Create outline indicator
        phase_indicator = QHBoxLayout()
        
        # Current phase indicator
        self.up_indicator = QLabel("↑")
        self.up_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(False))
        self.up_indicator.setAlignment(Qt.AlignCenter)
        
        self.down_indicator = QLabel("↓")
        self.down_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(False))
        self.down_indicator.setAlignment(Qt.AlignCenter)
        
        # Add to layout
        phase_indicator.addWidget(self.up_indicator)
        phase_indicator.addWidget(self.down_indicator)
        
        # Add to layout
        phase_layout.addLayout(phase_indicator)
        
        # Phase value display
        self.stage_value = QLabel(T.get("prepare"))
        self.stage_value.setStyleSheet("color: #3498db; font-size: 24pt; font-weight: bold;")
        self.stage_value.setAlignment(Qt.AlignCenter)
        self.stage_value.setFixedSize(180, 60)
        
        # Add current phase label
        phase_text_layout = QHBoxLayout()
        phase_text_layout.addWidget(self.stage_value, 0, Qt.AlignCenter)
        
        phase_layout.addLayout(phase_text_layout)
        
        # Leave some extra space for phase situation
        spacer = QWidget()
        spacer.setMinimumHeight(20)
        phase_layout.addWidget(spacer)
        
        self.content_layout.addWidget(self.phase_group)
    
    def _on_exercise_changed(self, exercise_display):
        """Exercise type change handler"""
        # Check if exercise_display is empty or not in mapping
        if not exercise_display or exercise_display not in self.exercise_code_map:
            return
            
        exercise_code = self.exercise_code_map[exercise_display]
        self.current_exercise = exercise_code
        self.exercise_changed.emit(exercise_code)
        self.update_counter_style()
    
    def _on_reset_counter(self):
        """Reset counter handler"""
        self.counter_reset.emit()
    

    def _on_rotation_toggled(self, checked):
        """Rotation mode toggle handler"""
        # Send signal
        self.rotation_toggled.emit(checked)
    
    def _on_skeleton_toggled(self, checked):
        """Skeleton display toggle handler"""
        # Send signal
        self.skeleton_toggled.emit(checked)
    

    
    def _on_mirror_toggled(self, checked):
        """镜像模式切换处理"""
        self.mirror_toggled.emit(checked)
    
    def _create_separator(self):
        """创建分隔线"""
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #bdc3c7;")
        return separator
    
    def _on_connect_source(self):
        """视频源连接按钮处理"""
        source_type = self.source_type_combo.currentData()
        source_input = self.source_url_input.text().strip()
        
        # 验证输入
        if not source_input:
            if source_type == "camera":
                source_input = "0"  # 默认摄像头
            else:
                self.source_status_label.setText("● 请输入URL")
                self.source_status_label.setStyleSheet("color: #e74c3c; font-size: 11pt;")
                return
        
        # 更新状态
        self.source_status_label.setText("● 连接中...")
        self.source_status_label.setStyleSheet("color: #f39c12; font-size: 11pt;")
        
        # 发送信号
        self.video_source_changed.emit(source_type, source_input)
    
    def update_source_status(self, connected, message=""):
        """更新视频源连接状态"""
        if connected:
            status_text = f"● 已连接{(' - ' + message) if message else ''}"
            self.source_status_label.setText(status_text)
            self.source_status_label.setStyleSheet("color: #27ae60; font-size: 11pt;")
        else:
            status_text = f"● 连接失败{(' - ' + message) if message else ''}"
            self.source_status_label.setText(status_text)
            self.source_status_label.setStyleSheet("color: #e74c3c; font-size: 11pt;")
    
    def _on_model_changed(self, index):
        """模型版本切换处理"""
        model_version = self.model_combo.currentData()
        print(f"[控制面板] 切换模型版本: {model_version}")
        self.model_changed.emit(model_version)
    
    def _on_tts_mode_changed(self, index):
        """TTS模式切换处理"""
        mode = self.tts_mode_combo.currentData()
        # 根据模式启用/禁用配置按钮
        self.ha_config_btn.setEnabled(mode == "ha")
        print(f"[控制面板] 切换TTS模式: {mode}")
        self.tts_mode_changed.emit(mode)
    
    def _open_ha_config(self):
        """打开HA配置对话框"""
        from ui.ha_config_dialog import HAConfigDialog
        import json
        
        # 加载当前配置
        config_path = 'data/tts_config.json'
        config = {}
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            pass
        
        # 打开对话框
        dialog = HAConfigDialog(self, config)
        if dialog.exec_():
            # 保存配置
            ha_config = dialog.get_config()
            
            # 确保保留完整配置结构
            if 'ha_config' not in config:
                config['ha_config'] = {}
            
            # 更新ha_config
            config['ha_config'].update(ha_config)
            
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
                print("[控制面板] HA配置已保存")
                
                # 重新加载配置到主窗口
                if hasattr(self.parent(), 'init_tts_manager'):
                    self.parent().init_tts_manager()
                    print("[控制面板] TTS配置已重新加载")
            except Exception as e:
                print(f"[错误] 保存HA配置失败: {e}")
                import traceback
                traceback.print_exc()
    
    def update_counter(self, value):
        """Update counter value"""
        old_count = int(self.counter_value.text() or "0")
        new_count = int(value)
        
        # Update counter display
        self.counter_value.setText(str(value))
        
        # If increased, show animation
        if new_count > old_count:
            self.show_success_animation()
    
    def update_angle(self, angle_text, exercise_type=None):
        """Update angle display"""
        if exercise_type:
            # Set angle text
            self.angle_value.setText(f"{angle_text}°")
            
            # Update color based on angle value and exercise type
            try:
                current_exercise = self.exercise_display_map.get(exercise_type, "bicep_curl")
                current_color = self.exercise_colors.get(current_exercise, "#3498db")
                
                # Determine if highlighting is needed
                highlight = False
                angle_value = float(angle_text)
                
                if exercise_type == "squat" and angle_value < 120:  # Squat lower limit point
                    highlight = True
                elif exercise_type == "pushup" and angle_value < 100:  # Pushup lower limit point
                    highlight = True
                elif exercise_type == "leg_raise" and angle_value > 90:  # Leg raise upper limit point
                    highlight = True
                elif exercise_type == "knee_raise" and angle_value > 100:  # Knee raise upper limit point
                    highlight = True
                elif exercise_type == "knee_press" and (angle_value < 100 or angle_value > 160):  # Knee press key points
                    highlight = True
                
                # Set style
                self.angle_value.setStyleSheet(AppStyles.get_angle_value_style(current_color, highlight))
            except Exception as e:
                print(f"Error updating angle style: {e}")
    
    def update_phase(self, stage):
        """Update phase display"""
        if stage == "up":
            self.stage_value.setText(T.get("up"))
            self.up_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(True))
            self.down_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(False))
        elif stage == "down":
            self.stage_value.setText(T.get("down"))
            self.up_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(False))
            self.down_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(True))
        else:
            self.stage_value.setText(T.get("prepare"))
            self.up_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(False))
            self.down_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(False))
    
    def update_stage(self, stage, exercise_type):
        """Update exercise stage"""
        if not stage:
            return
            
        self.stage_value.setText(stage)
        
        try:
            # Update stage indicator
            current_exercise = self.exercise_display_map.get(exercise_type, "")
            
            # If preset color not found, use default color
            if current_exercise in AppStyles.EXERCISE_COLORS:
                current_color = AppStyles.EXERCISE_COLORS[current_exercise]
            else:
                current_color = "#3498db"  # Default use blue
            
            if stage == "up":
                self.up_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(True, current_color))
                self.down_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(False))
            elif stage == "down":
                self.down_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(True, current_color))
                self.up_indicator.setStyleSheet(AppStyles.get_phase_indicator_style(False))
        except Exception as e:
            print(f"Error in update_stage: {e}")
            # Use default color on error
            current_color = "#3498db"
    
    def show_success_animation(self):
        """Show success animation for counter increase"""
        self.counter_value.setStyleSheet(AppStyles.get_success_counter_style())
    
    def update_counter_style(self):
        """Update counter style to current exercise color"""
        try:
            # Get current exercise type display name
            current_exercise = self.exercise_display_map.get(self.current_exercise, "")
            
            # If preset color not found, use default color
            if current_exercise in AppStyles.EXERCISE_COLORS:
                current_color = AppStyles.EXERCISE_COLORS[current_exercise]
            else:
                current_color = "#3498db"  # Default use blue
                
            self.counter_value.setStyleSheet(AppStyles.get_counter_value_style(current_color))
        except Exception as e:
            print(f"Error in update_counter_style: {e}")
            # Use default color on error
            self.counter_value.setStyleSheet(AppStyles.get_counter_value_style("#3498db"))
    
    def reset_counter_style(self):
        """Reset counter style"""
        try:
            # Get current exercise type display name
            current_exercise = self.exercise_display_map.get(self.current_exercise, "")
            
            # If preset color not found, use default color
            if current_exercise in AppStyles.EXERCISE_COLORS:
                current_color = AppStyles.EXERCISE_COLORS[current_exercise]
            else:
                current_color = "#3498db"  # Default use blue
                
            self.counter_value.setStyleSheet(AppStyles.get_counter_value_style(current_color))
        except Exception as e:
            print(f"Error in reset_counter_style: {e}")
            # Use default color on error
            self.counter_value.setStyleSheet(AppStyles.get_counter_value_style("#3498db"))
        
    def update_language(self):
        """Update interface language"""
        # Reload exercise type mappings from JSON file (with updated translations)
        self.exercise_display_map = self.load_exercise_display_map()
        
        # Update model type mappings
        self.model_display_map = {
            "lightweight": T.get("lightweight"),
            "balanced": T.get("balanced"),
            "performance": T.get("performance")
        }
        
        # Update reverse mappings
        self.exercise_code_map = {v: k for k, v in self.exercise_display_map.items()}
        
        # Update UI text
        self.title_label.setText(T.get("app_title"))
        self.controls_group.setTitle(T.get("control_options"))
        self.info_group.setTitle(T.get("exercise_data"))
        self.phase_group.setTitle(T.get("motion_detection"))
        
        self.counter_label.setText(T.get("count_completed"))
        self.exercise_label.setText(T.get("exercise_type"))

        
        # Update switch text
        self.skeleton_switch.label.setText(T.get("skeleton_display"))
        self.mirror_switch.label.setText(T.get("mirror_mode"))
        
        # Update button text
        self.increase_button.setText(T.get("increase"))
        self.decrease_button.setText(T.get("decrease"))
        self.reset_button.setText(T.get("reset"))
        self.confirm_button.setText(T.get("confirm"))
        
        # Update phase label
        self.phase_title.setText(T.get(self.current_phase) if hasattr(self, "current_phase") else "")
        
        # Update combo boxes
        self._update_combo_items(self.exercise_combo, self.exercise_display_map)

    def _update_combo_items(self, combo_box, item_map):
        """Update combo box content"""
        # Save current selected data
        current_data = combo_box.currentData()
        current_text = combo_box.currentText()
        
        # Clear combo box
        combo_box.clear()
        
        # Refill options
        for code, display in item_map.items():
            combo_box.addItem(display, code)
        
        # Try to restore previously selected item
        if current_data:
            # If there's data, restore based on data
            for i in range(combo_box.count()):
                if combo_box.itemData(i) == current_data:
                    combo_box.setCurrentIndex(i)
                    break
        elif current_text:
            # Otherwise try to restore based on text
            for i in range(combo_box.count()):
                if combo_box.itemText(i) == current_text:
                    combo_box.setCurrentIndex(i)
                    break
    
    def restore_from_settings(self, settings_manager):
        """Restore control panel UI state from settings"""
        try:
            # Restore exercise type
            saved_exercise = settings_manager.get('exercise_type', 'overhead_press')
            if saved_exercise in self.exercise_display_map:
                display_name = self.exercise_display_map[saved_exercise]
                index = self.exercise_combo.findText(display_name)
                if index >= 0:
                    self.exercise_combo.setCurrentIndex(index)
                    print(f"[ControlPanel] 恢复运动类型: {saved_exercise}")
            
            # Restore TTS mode
            saved_tts = settings_manager.get('tts_mode', 'sound')
            tts_display_map = {'sound': '本地音效', 'ha': 'HA语音播报'}
            if saved_tts in tts_display_map:
                index = self.tts_mode_combo.findText(tts_display_map[saved_tts])
                if index >= 0:
                    self.tts_mode_combo.setCurrentIndex(index)
                    print(f"[ControlPanel] 恢复TTS模式: {saved_tts}")
            
            # Restore mirror mode
            saved_mirror = settings_manager.get('mirror_mode', True)
            self.mirror_switch.setChecked(saved_mirror)
            print(f"[ControlPanel] 恢复镜像模式: {saved_mirror}")
            
        except Exception as e:
            print(f"[ControlPanel] 恢复设置失败: {e}")
            import traceback
            traceback.print_exc()

