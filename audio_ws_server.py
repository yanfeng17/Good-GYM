#!/usr/bin/env python3
"""
WebSocket Audio Server for Browser Audio Playback
- Runs WebSocket server on port 8765
- Serves audio files via HTTP on port 8766
- Broadcasts audio play events to connected browsers
"""

import asyncio
import json
import os
import sys
import base64
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

# Configuration
AUTH_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'auth.json')

def load_auth():
    if not os.path.exists(AUTH_FILE):
        return None
    try:
        with open(AUTH_FILE, 'r') as f:
            return json.load(f)
    except:
        return None

def save_auth(username, password):
    data = {'username': username, 'password': password}
    os.makedirs(os.path.dirname(AUTH_FILE), exist_ok=True)
    with open(AUTH_FILE, 'w') as f:
        json.dump(data, f)

def get_setup_page(error=None):
    error_html = f'<div style="color:red;margin-bottom:10px;">{error}</div>' if error else ''
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Good-GYM Setup</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f0f2f5; margin: 0; }}
        .card {{ background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); width: 100%; max-width: 320px; }}
        h2 {{ text-align: center; color: #1a1a1a; margin-top: 0; }}
        label {{ display: block; margin-bottom: 0.5rem; color: #4a5568; font-size: 0.875rem; font-weight: 500; }}
        input {{ width: 100%; padding: 0.75rem; margin-bottom: 1rem; border: 1px solid #e2e8f0; border-radius: 0.375rem; box-sizing: border-box; }}
        input:focus {{ outline: none; border-color: #3182ce; ring: 2px solid #3182ce; }}
        button {{ width: 100%; padding: 0.75rem; background: #3182ce; color: white; border: none; border-radius: 0.375rem; font-weight: 600; cursor: pointer; transition: background 0.2s; }}
        button:hover {{ background: #2c5282; }}
    </style>
</head>
<body>
    <div class="card">
        <h2>🏋️‍♂️ Good-GYM Setup</h2>
        <p style="text-align:center;color:#718096;margin-bottom:1.5rem;">请设置访问账号密码</p>
        {error_html}
        <form method="POST" action="/setup">
            <label>用户名 (默认 admin)</label>
            <input type="text" name="username" value="admin" required>
            <label>密码</label>
            <input type="password" name="password" required placeholder="设置您的密码">
            <button type="submit">完成设置</button>
        </form>
    </div>
</body>
</html>
""".encode('utf-8')

class AudioHTTPHandler(SimpleHTTPRequestHandler):
    """HTTP handler for serving audio files with Basic Auth"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=AUDIO_DIR, **kwargs)
    
    def log_message(self, format, *args):
        # Reduce log noise
        pass
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def do_POST(self):
        """Handle Setup POST"""
        auth_data = load_auth()
        if not auth_data and self.path == '/setup':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')
                params = urllib.parse.parse_qs(post_data)
                
                user = params.get('username', ['admin'])[0]
                pwd = params.get('password', [''])[0]
                
                if user and pwd:
                    save_auth(user, pwd)
                    self.send_response(302)
                    self.send_header('Location', '/')
                    self.end_headers()
                    return
            except Exception as e:
                print(f"Setup Error: {e}", flush=True)
            
            # Error case
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(get_setup_page("无效的请求"))
            return
            
        self.send_error(405)

    def do_GET(self):
        """Handle GET requests with Auth"""
        auth_data = load_auth()
        
        # 1. SETUP FLOW: If no auth defined
        if not auth_data:
            if self.path == '/setup':
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(get_setup_page())
                return
            else:
                # Redirect everything to setup
                self.send_response(302)
                self.send_header('Location', '/setup')
                self.end_headers()
                return

        # 2. CHECK HEADER
        # Allow Basic Auth
        target_header = f"Basic {base64.b64encode(f'{auth_data['username']}:{auth_data['password']}'.encode()).decode()}"
        auth_header = self.headers.get('Authorization')
        
        if not auth_header or auth_header != target_header:
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Good-GYM Login"')
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b'Authorization required.')
            return

        # 3. NORMAL FLOW
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/vnc_audio.html')
            self.end_headers()
            return
        
        if self.path.endswith('vnc_audio.html'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            
            try:
                with open(os.path.join(AUDIO_DIR, 'vnc_audio.html'), 'rb') as f:
                    self.wfile.write(f.read())
            except Exception as e:
                pass # Should send error but here we just pass
            return
            
        super().do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def run_http_server():
    """Run HTTP server for audio files"""
    try:
        server = HTTPServer(('0.0.0.0', AUDIO_HTTP_PORT), AudioHTTPHandler)
        print(f"[AudioHTTP] ✓ HTTP服务器启动在端口 {AUDIO_HTTP_PORT}", flush=True)
        server.serve_forever()
    except Exception as e:
        print(f"[AudioHTTP] ✗ HTTP服务器启动失败: {e}", flush=True)

async def main():
    """Main entry point"""
    global event_loop
    
    # Get the running event loop
    event_loop = asyncio.get_running_loop()
    
    # Start HTTP server in background thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Start internal event listener in background thread
    event_thread = threading.Thread(target=run_event_listener, daemon=True)
    event_thread.start()
    
    # Start WebSocket server
    print(f"[AudioWS] ✓ WebSocket服务器启动在端口 {AUDIO_WS_PORT}", flush=True)
    
    async with websockets.serve(handle_client, "0.0.0.0", AUDIO_WS_PORT):
        print(f"[AudioWS] ========== 服务器就绪 ==========", flush=True)
        await asyncio.Future()  # Run forever

# Internal event listener for receiving events from SoundManager
INTERNAL_EVENT_PORT = 8865
event_loop = None

def run_event_listener():
    """Run internal TCP listener for SoundManager events"""
    global event_loop
    
    import socket
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind(('0.0.0.0', INTERNAL_EVENT_PORT))
        server_socket.listen(5)
        print(f"[AudioEvent] ✓ 内部事件监听器启动在端口 {INTERNAL_EVENT_PORT}", flush=True)
        
        while True:
            try:
                client_socket, addr = server_socket.accept()
                data = client_socket.recv(1024).decode('utf-8')
                client_socket.close()
                
                if data:
                    print(f"[AudioEvent] 收到事件: {data}", flush=True)
                    try:
                        event_data = json.loads(data)
                        if event_data.get('type') == 'play_audio':
                            sound_type = event_data.get('sound', 'count')
                            count = event_data.get('count')
                            # Schedule broadcast in the async event loop
                            if event_loop:
                                asyncio.run_coroutine_threadsafe(
                                    broadcast_audio_event(sound_type, count), 
                                    event_loop
                                )
                    except json.JSONDecodeError:
                        pass
                        
            except Exception as e:
                print(f"[AudioEvent] 处理错误: {e}", flush=True)
                
    except Exception as e:
        print(f"[AudioEvent] ✗ 监听器启动失败: {e}", flush=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[AudioWS] 服务器关闭", flush=True)
    except Exception as e:
        print(f"[AudioWS] ✗ 服务器错误: {e}", flush=True)
        import traceback
        traceback.print_exc()
