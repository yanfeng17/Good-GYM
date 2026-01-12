from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QComboBox, QTableWidget,
                             QTableWidgetItem, QCheckBox, QTextEdit, QGroupBox,
                             QSpinBox, QMessageBox, QHeaderView, QWidget, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
import json
import os

class ParameterRow(QWidget):
    """单个参数行组件"""
    delete_requested = pyqtSignal(object)  # 发送自己的引用
    
    def __init__(self, key="", param_type="string", value="", enabled=True, use_variables=False):
        super().__init__()
        self.init_ui(key, param_type, value, enabled, use_variables)
    
    def init_ui(self, key, param_type, value, enabled, use_variables):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 启用复选框
        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(enabled)
        layout.addWidget(self.enabled_check)
        
        # 键名输入
        self.key_input = QLineEdit(key)
        self.key_input.setPlaceholderText("参数名...")
        layout.addWidget(self.key_input)
        
        # 类型选择
        self.type_combo = QComboBox()
        self.type_combo.addItems(["string", "number", "boolean", "object", "array"])
        self.type_combo.setCurrentText(param_type)
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        layout.addWidget(self.type_combo)
        
        # 值输入容器
        self.value_container = QWidget()
        self.value_layout = QHBoxLayout()
        self.value_layout.setContentsMargins(0, 0, 0, 0)
        self.value_container.setLayout(self.value_layout)
        self.create_value_widget(param_type, value)
        layout.addWidget(self.value_container, 1)
        
        # 变量替换复选框（仅string类型）
        self.var_check = QCheckBox("使用变量")
        self.var_check.setChecked(use_variables)
        self.var_check.setVisible(param_type == "string")
        layout.addWidget(self.var_check)
        
        # 删除按钮
        delete_btn = QPushButton("✕")
        delete_btn.setMaximumWidth(30)
        delete_btn.setStyleSheet("QPushButton { color: red; font-weight: bold; }")
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self))
        layout.addWidget(delete_btn)
        
        self.setLayout(layout)
    
    def create_value_widget(self, param_type, value):
        """根据类型创建值输入控件"""
        # 清空现有控件
        while self.value_layout.count():
            child = self.value_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if param_type == "string":
            # 确保value是字符串
            str_value = str(value) if value is not None else ""
            self.value_widget = QLineEdit(str_value)
            self.value_widget.setPlaceholderText("值 (支持{count}等变量)...")
            self.value_layout.addWidget(self.value_widget)
            
        elif param_type == "number":
            self.value_widget = QSpinBox()
            self.value_widget.setRange(-999999, 999999)
            self.value_widget.setValue(int(value) if value else 0)
            self.value_layout.addWidget(self.value_widget)
            
        elif param_type == "boolean":
            self.value_widget = QComboBox()
            self.value_widget.addItems(["false", "true"])
            self.value_widget.setCurrentText("true" if value else "false")
            self.value_layout.addWidget(self.value_widget)
            
        elif param_type in ["object", "array"]:
            self.value_widget = QTextEdit()
            self.value_widget.setMaximumHeight(60)
            self.value_widget.setPlaceholderText("JSON格式...")
            try:
                self.value_widget.setPlainText(json.dumps(value, ensure_ascii=False, indent=2))
            except:
                self.value_widget.setPlainText(str(value))
            self.value_layout.addWidget(self.value_widget)
        
        # 更新var_check可见性（修复bug）
        if hasattr(self, 'var_check') and self.var_check:
            self.var_check.setVisible(param_type == "string")
    
    def on_type_changed(self, new_type):
        """类型改变时重新创建值控件"""
        current_value = self.get_value()
        self.create_value_widget(new_type, current_value)
        self.var_check.setVisible(new_type == "string")
    
    def get_value(self):
        """获取当前值"""
        param_type = self.type_combo.currentText()
        
        if param_type == "string":
            return self.value_widget.text()
        elif param_type == "number":
            return self.value_widget.value()
        elif param_type == "boolean":
            return self.value_widget.currentText() == "true"
        elif param_type in ["object", "array"]:
            try:
                return json.loads(self.value_widget.toPlainText())
            except:
                return self.value_widget.toPlainText()
    
    def get_param_data(self):
        """获取参数数据"""
        param_data = {
            "key": self.key_input.text(),
            "type": self.type_combo.currentText(),
            "value": self.get_value(),
            "enabled": self.enabled_check.isChecked(),
            "use_variables": self.var_check.isChecked() if self.type_combo.currentText() == "string" else False
        }
        # 调试日志
        return param_data


class HAConfigDialog(QDialog):
    """Home Assistant API配置对话框"""
    
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config or {}
        self.param_rows = []
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        self.setWindowTitle("Home Assistant API 配置")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        
        # 创建标签页
        tabs = QTabWidget()
        
        # 基础设置标签
        basic_tab = self.create_basic_tab()
        tabs.addTab(basic_tab, "基础设置")
        
        # 参数设置标签  
        params_tab = self.create_params_tab()
        tabs.addTab(params_tab, "参数设置")
        
        # 预览标签
        preview_tab = self.create_preview_tab()
        tabs.addTab(preview_tab, "预览")
        
        layout.addWidget(tabs)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        
        test_btn = QPushButton("测试连接")
        test_btn.clicked.connect(self.test_connection)
        button_layout.addWidget(test_btn)
        
        button_layout.addStretch()
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_basic_tab(self):
        """创建基础设置标签"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # HA地址
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("HA地址:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("http://192.168.31.45:8123")
        url_layout.addWidget(self.url_input, 1)
        layout.addLayout(url_layout)
        
        # Token
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("Token:"))
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("长期访问令牌...")
        self.token_input.setEchoMode(QLineEdit.Password)
        token_layout.addWidget(self.token_input, 1)
        
        self.show_token_btn = QPushButton("👁")
        self.show_token_btn.setMaximumWidth(40)
        self.show_token_btn.setCheckable(True)
        self.show_token_btn.toggled.connect(self.toggle_token_visibility)
        token_layout.addWidget(self.show_token_btn)
        layout.addLayout(token_layout)
        
        # 服务路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("服务路径:"))
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("/api/services/xiaomi_miot/intelligent_speaker")
        path_layout.addWidget(self.path_input, 1)
        layout.addLayout(path_layout)
        
        # 预设选择
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("预设模板:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItem("（自定义）", None)
        self.preset_combo.addItem("小米音箱TTS", "xiaomi_speaker_tts")
        self.preset_combo.addItem("HA通知", "ha_notification")
        self.preset_combo.currentIndexChanged.connect(self.load_preset)
        preset_layout.addWidget(self.preset_combo, 1)
        layout.addLayout(preset_layout)
        
        # 可用变量提示
        var_group = QGroupBox("可用变量")
        var_layout = QVBoxLayout()
        var_layout.addWidget(QLabel("• {count} - 当前次数"))
        var_layout.addWidget(QLabel("• {exercise} - 运动名称（中文）"))
        var_layout.addWidget(QLabel("• {total} - 目标次数"))
        var_group.setLayout(var_layout)
        layout.addWidget(var_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_params_tab(self):
        """创建参数设置标签"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("请求Body参数:")
        title_font = QFont()
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # 参数列表容器
        self.params_container = QWidget()
        self.params_layout = QVBoxLayout()
        self.params_layout.setSpacing(5)
        self.params_container.setLayout(self.params_layout)
        
        from PyQt5.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidget(self.params_container)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll, 1)
        
        # 添加参数按钮
        add_btn = QPushButton("+ 添加参数")
        add_btn.clicked.connect(self.add_parameter)
        layout.addWidget(add_btn)
        
        widget.setLayout(layout)
        return widget
    
    def create_preview_tab(self):
        """创建预览标签"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        preview_label = QLabel("请求预览（示例：count=5）:")
        layout.addWidget(preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.preview_text)
        
        refresh_btn = QPushButton("刷新预览")
        refresh_btn.clicked.connect(self.update_preview)
        layout.addWidget(refresh_btn)
        
        widget.setLayout(layout)
        return widget
    
    def add_parameter(self, key="", param_type="string", value="", enabled=True, use_variables=False):
        """添加参数行"""
        param_row = ParameterRow(key, param_type, value, enabled, use_variables)
        param_row.delete_requested.connect(self.remove_parameter)
        self.param_rows.append(param_row)
        self.params_layout.addWidget(param_row)
    
    def remove_parameter(self, param_row):
        """删除参数行"""
        if param_row in self.param_rows:
            self.param_rows.remove(param_row)
            self.params_layout.removeWidget(param_row)
            param_row.deleteLater()
    
    def toggle_token_visibility(self, checked):
        """切换Token显示/隐藏"""
        if checked:
            self.token_input.setEchoMode(QLineEdit.Normal)
        else:
            self.token_input.setEchoMode(QLineEdit.Password)
    
    def load_preset(self, index):
        """加载预设配置"""
        preset_key = self.preset_combo.currentData()
        if not preset_key:
            return
        
        # 从配置文件加载预设
        config_path = os.path.join('data', 'tts_config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                preset = config.get('presets', {}).get(preset_key, {})
                
                if preset:
                    self.path_input.setText(preset.get('service_path', ''))
                    
                    # 清空现有参数
                    for row in self.param_rows[:]:
                        self.remove_parameter(row)
                    
                    # 加载预设参数
                    for param in preset.get('body_params', []):
                        self.add_parameter(
                            param.get('key', ''),
                            param.get('type', 'string'),
                            param.get('value', ''),
                            param.get('enabled', True),
                            param.get('use_variables', False)
                        )
    
    def load_config(self):
        """加载配置"""
        ha_config = self.config.get('ha_config', {})
        
        self.url_input.setText(ha_config.get('base_url', ''))
        self.token_input.setText(ha_config.get('token', ''))
        self.path_input.setText(ha_config.get('service_path', ''))
        
        # 加载参数
        for param in ha_config.get('body_params', []):
            self.add_parameter(
                param.get('key', ''),
                param.get('type', 'string'),
                param.get('value', ''),
                param.get('enabled', True),
                param.get('use_variables', False)
            )
    
    def get_config(self):
        """获取配置"""
        params = []
        for row in self.param_rows:
            params.append(row.get_param_data())
        
        return {
            'base_url': self.url_input.text(),
            'token': self.token_input.text(),
            'service_path': self.path_input.text(),
            'body_params': params
        }
    
    def update_preview(self):
        """更新预览"""
        from core.ha_api_manager import HAAPIManager
        
        config = self.get_config()
        manager = HAAPIManager(config['base_url'], config['token'])
        
        # 模拟变量
        variables = {'count': 5, 'exercise': '深蹲', 'total': 10}
        body = manager.prepare_body_with_variables(config['body_params'], variables)
        
        preview = f"POST {config['base_url']}{config['service_path']}\n\n"
        preview += "Headers:\n"
        preview += f"  Authorization: Bearer {'*' * 20}...\n"
        preview += "  Content-Type: application/json\n\n"
        preview += "Body:\n"
        preview += json.dumps(body, ensure_ascii=False, indent=2)
        
        self.preview_text.setPlainText(preview)
    
    def test_connection(self):
        """测试连接"""
        from core.ha_api_manager import HAAPIManager
        
        config = self.get_config()
        manager = HAAPIManager(config['base_url'], config['token'])
        
        success, message = manager.test_connection()
        
        if success:
            QMessageBox.information(self, "测试成功", message)
        else:
            QMessageBox.warning(self, "测试失败", message)
