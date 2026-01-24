import json
import os
import sys
from PyQt5.QtCore import QObject, pyqtSignal

class VideoSourceManager(QObject):
    """视频源管理器"""
    source_changed = pyqtSignal(str, object)  # 源类型, 配置
    
    def __init__(self):
        super().__init__()
        self.config_file = self.get_config_path()
        self.config = self.load_config()
        
    def get_config_path(self):
        """获取配置文件路径"""
        if getattr(sys, 'frozen', False):
            # 打包环境
            exe_dir = os.path.dirname(sys.executable)
            config_file = os.path.join(exe_dir, 'data', 'video_sources.json')
        else:
            # 开发或Docker环境
            # 首先尝试Docker容器的绝对路径
            docker_path = '/app/data/video_sources.json'
            if os.path.exists(docker_path):
                print(f"[VideoSourceManager] 使用Docker路径: {docker_path}")
                return docker_path
            # 回退到相对路径用于本地开发
            config_file = os.path.join('data', 'video_sources.json')
        return config_file
    
    def load_config(self):
        """加载配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 返回默认配置
                return self.get_default_config()
        except Exception as e:
            print(f"加载视频源配置失败: {e}")
            return self.get_default_config()
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            "current_source": "local_camera",
            "sources": {
                "local_camera": {
                    "type": "camera",
                    "device_id": 0,
                    "name": "本地摄像头"
                }
            },
            "presets": {}
        }
    
    def save_config(self):
        """保存配置"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"视频源配置已保存到: {self.config_file}")
            return True
        except Exception as e:
            print(f"保存视频源配置失败: {e}")
            return False
    
    def get_current_source(self):
        """获取当前视频源"""
        source_name = self.config.get('current_source', 'local_camera')
        return self.config['sources'].get(source_name)
    
    def set_current_source(self, source_name):
        """设置当前视频源"""
        if source_name in self.config['sources']:
            self.config['current_source'] = source_name
            self.save_config()
            source_config = self.config['sources'][source_name]
            self.source_changed.emit(source_config['type'], source_config)
            return True
        return False
    
    def add_source(self, name, source_type, **kwargs):
        """添加新视频源"""
        self.config['sources'][name] = {
            'type': source_type,
            'name': kwargs.get('display_name', name),
            **kwargs
        }
        self.save_config()
    
    def update_source(self, name, **kwargs):
        """更新视频源配置"""
        if name in self.config['sources']:
            self.config['sources'][name].update(kwargs)
            self.save_config()
            return True
        return False
    
    def remove_source(self, name):
        """删除视频源"""
        if name in self.config['sources'] and name != 'local_camera':
            del self.config['sources'][name]
            if self.config['current_source'] == name:
                self.config['current_source'] = 'local_camera'
            self.save_config()
            return True
        return False
    
    def get_all_sources(self):
        """获取所有视频源"""
        return self.config['sources']
    
    def get_presets(self):
        """获取预设模板"""
        return self.config.get('presets', {})
    
    def validate_url(self, url):
        """验证URL格式"""
        url = url.strip()
        if url.startswith('rtsp://'):
            return True, "RTSP"
        elif url.startswith('http://') or url.startswith('https://'):
            return True, "HTTP"
        elif url.isdigit():
            return True, "CAMERA"
        else:
            return False, "未知格式"
    
    def parse_camera_url(self, url_or_id):
        """解析摄像头URL或ID"""
        url_or_id = str(url_or_id).strip()
        
        # 本地摄像头ID
        if url_or_id.isdigit():
            return {
                'type': 'camera',
                'device_id': int(url_or_id)
            }
        
        # RTSP
        elif url_or_id.startswith('rtsp://'):
            return {
                'type': 'rtsp',
                'url': url_or_id
            }
        
        # HTTP
        elif url_or_id.startswith('http://') or url_or_id.startswith('https://'):
            return {
                'type': 'http',
                'url': url_or_id
            }
        
        return None
