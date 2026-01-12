import os
import sys
import subprocess
import threading
import socket
import json
from PyQt5.QtCore import QUrl, QObject
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

class SoundManager(QObject):
    """Sound effect management class for playing various notification sounds
    
    In Docker environment, also sends WebSocket events for browser audio playback.
    """
    
    # WebSocket server settings
    WS_HOST = 'localhost'
    WS_PORT = 8765
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.use_docker = False
        self.use_websocket = False
        self.audio_tool = None
        self.init_sounds()
    
    def init_sounds(self):
        """Initialize all sound effects"""
        try:
            print("[SoundManager] ========== 初始化音效管理器 ==========", flush=True)
            
            # Set paths for various sound effects
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            print(f"[SoundManager] 基础目录: {base_dir}", flush=True)
            
            # Check for Docker environment
            docker_assets = '/app/assets'
            if os.path.exists(docker_assets):
                print(f"[SoundManager] ✓ Docker环境检测到", flush=True)
                assets_dir = docker_assets
                self.use_docker = True
                # Enable WebSocket for browser audio
                self.use_websocket = True
            else:
                assets_dir = os.path.join(base_dir, "assets")
                print(f"[SoundManager] 使用本地资源路径: {assets_dir}", flush=True)
                self.use_docker = False
                self.use_websocket = False
            
            self.count_sound_path = os.path.join(assets_dir, "count.mp3")
            self.succeed_sound_path = os.path.join(assets_dir, "succeed.mp3")
            self.milestone_sound_path = os.path.join(assets_dir, "milestone.mp3")
            
            # Verify files exist and log
            self.count_file_exists = os.path.exists(self.count_sound_path)
            self.succeed_file_exists = os.path.exists(self.succeed_sound_path)
            self.milestone_file_exists = os.path.exists(self.milestone_sound_path)
            
            print(f"[SoundManager] 音效文件状态:", flush=True)
            print(f"  - count.mp3: {'✓存在' if self.count_file_exists else '✗不存在'}", flush=True)
            print(f"  - succeed.mp3: {'✓存在' if self.succeed_file_exists else '✗不存在'}", flush=True)
            print(f"  - milestone.mp3: {'✓存在' if self.milestone_file_exists else '✗不存在'}", flush=True)
            
            # Initialize audio based on environment
            if self.use_docker:
                self._check_audio_tools()
                print(f"[SoundManager] WebSocket音频: {'✓启用' if self.use_websocket else '✗禁用'}", flush=True)
            else:
                self.init_sound_players()
            
            print("[SoundManager] ========== 音效管理器初始化完成 ==========", flush=True)
            
        except Exception as e:
            print(f"[SoundManager] ✗ 初始化失败: {e}", flush=True)
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
    
    def _check_audio_tools(self):
        """Check which audio playback tool is available"""
        self.audio_tool = None
        tools = ['ffplay', 'mpv', 'paplay', 'aplay']
        
        for tool in tools:
            try:
                result = subprocess.run(['which', tool], capture_output=True, text=True)
                if result.returncode == 0:
                    self.audio_tool = tool
                    print(f"[SoundManager] ✓ 本地播放工具: {tool}", flush=True)
                    break
            except:
                pass
        
        if not self.audio_tool:
            print("[SoundManager] ⚠ 未找到本地音频播放工具", flush=True)
    
    def init_sound_players(self):
        """Initialize Qt media players for desktop environment"""
        self.count_sound = QMediaPlayer(self)
        if self.count_file_exists:
            self.count_sound.setMedia(QMediaContent(QUrl.fromLocalFile(self.count_sound_path)))
            self.count_sound.setVolume(80)  
        
        self.succeed_player = QMediaPlayer(self)
        if self.succeed_file_exists:
            self.succeed_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.succeed_sound_path)))
            self.succeed_player.setVolume(80)
            
        self.milestone_player = QMediaPlayer(self)
        if self.milestone_file_exists:
            self.milestone_player.setMedia(QMediaContent(QUrl.fromLocalFile(self.milestone_sound_path)))
            self.milestone_player.setVolume(85)
    
    def _send_ws_audio_event(self, sound_type, count=None):
        """Send audio event via WebSocket to browser clients"""
        def send_async():
            try:
                # Simple HTTP request to trigger audio (using a simpler approach)
                # The WebSocket server handles broadcasting to connected clients
                import http.client
                conn = http.client.HTTPConnection(self.WS_HOST, self.WS_PORT, timeout=2)
                
                # Use a special endpoint to trigger audio
                msg_data = {
                    "type": "play_audio",
                    "sound": sound_type
                }
                if count is not None:
                    msg_data["count"] = count
                    
                message = json.dumps(msg_data)
                
                # Try to connect to WebSocket server via simple TCP
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                sock.connect((self.WS_HOST, self.WS_PORT + 100))  # Port 8865 for internal events
                sock.send(message.encode())
                sock.close()
                print(f"[SoundManager-WS] ✓ 发送音频事件: {sound_type} (count={count})", flush=True)
                
            except ConnectionRefusedError:
                print(f"[SoundManager-WS] ⚠ WebSocket服务器未就绪", flush=True)
            except Exception as e:
                print(f"[SoundManager-WS] ⚠ 发送失败: {e}", flush=True)
        
        thread = threading.Thread(target=send_async, daemon=True)
        thread.start()
    
    def _play_with_command(self, filepath):
        """Play audio using system command in background thread"""
        def play_async():
            try:
                if self.audio_tool == 'ffplay':
                    cmd = ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'warning', filepath]
                elif self.audio_tool == 'mpv':
                    cmd = ['mpv', '--no-video', '--really-quiet', filepath]
                elif self.audio_tool == 'paplay':
                    cmd = ['paplay', filepath]
                else:
                    cmd = ['ffplay', '-nodisp', '-autoexit', '-loglevel', 'warning', filepath]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode != 0 and result.stderr:
                    print(f"[SoundManager] ⚠ 本地播放警告: {result.stderr[:200]}", flush=True)
                    
            except subprocess.TimeoutExpired:
                print(f"[SoundManager] ⚠ 播放超时", flush=True)
            except Exception as e:
                print(f"[SoundManager] ✗ 播放异常: {e}", flush=True)
        
        thread = threading.Thread(target=play_async, daemon=True)
        thread.start()
    
    def play_count_sound(self, count=None):
        """Play count sound effect"""
        print(f"[SoundManager] 播放计数音效 (count={count})", flush=True)
        
        if self.use_docker:
            # In Docker: send WebSocket event for browser playback
            if self.use_websocket:
                self._send_ws_audio_event('count', count)
            
            # Also try local playback as backup
            if self.audio_tool and self.count_file_exists:
                self._play_with_command(self.count_sound_path)
        else:
            # Desktop: use Qt player
            if self.count_file_exists:
                self.count_sound.stop()
                self.count_sound.setPosition(0)
                self.count_sound.play()
    
    def play_milestone_sound(self, count):
        """Play milestone notification sound (every 10 counts)"""
        if count > 0 and count % 10 == 0:
            print(f"[SoundManager] 播放里程碑音效 (第{count}次)", flush=True)
            
            if self.use_docker:
                if self.use_websocket:
                    self._send_ws_audio_event('milestone', count)
                if self.audio_tool and self.milestone_file_exists:
                    self._play_with_command(self.milestone_sound_path)
            else:
                if self.milestone_file_exists:
                    self.milestone_player.setPosition(0)
                    self.milestone_player.play()
    
    def play_completion_sound(self):
        """Play completion notification sound"""
        print(f"[SoundManager] 播放完成音效", flush=True)
        
        if self.use_docker:
            if self.use_websocket:
                self._send_ws_audio_event('succeed')
            if self.audio_tool and self.succeed_file_exists:
                self._play_with_command(self.succeed_sound_path)
        else:
            if self.succeed_file_exists:
                self.succeed_player.setPosition(0)
                self.succeed_player.play()
