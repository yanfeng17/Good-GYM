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
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

try:
    import websockets
except ImportError:
    print("[AudioWS] ERROR: websockets library not installed", flush=True)
    print("[AudioWS] Install with: pip install websockets", flush=True)
    sys.exit(1)

# Global set of connected clients
connected_clients = set()

AUDIO_WS_PORT = 8765
AUDIO_HTTP_PORT = 8080
AUDIO_DIR = "/app"  # Serve entire /app directory (includes vnc_audio.html and assets/)

print(f"[AudioWS] ========== 音频WebSocket服务器启动 ==========", flush=True)
print(f"[AudioWS] WebSocket端口: {AUDIO_WS_PORT}", flush=True)
print(f"[AudioWS] HTTP端口: {AUDIO_HTTP_PORT}", flush=True)
print(f"[AudioWS] 音频目录: {AUDIO_DIR}", flush=True)

async def handle_client(websocket):
    """Handle WebSocket client connection"""
    client_id = id(websocket)
    print(f"[AudioWS] ✓ 客户端连接: {client_id}", flush=True)
    connected_clients.add(websocket)
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            "type": "connected",
            "message": "Audio WebSocket connected",
            "client_id": client_id
        }))
        print(f"[AudioWS] 发送欢迎消息给客户端 {client_id}", flush=True)
        
        # Keep connection alive with ping-pong
        while True:
            try:
                # Wait for message with timeout (allows checking connection)
                message = await asyncio.wait_for(websocket.recv(), timeout=30)
                print(f"[AudioWS] 收到消息从 {client_id}: {message}", flush=True)
                
                try:
                    data = json.loads(message)
                    if data.get("type") == "ping":
                        await websocket.send(json.dumps({"type": "pong"}))
                except json.JSONDecodeError:
                    pass
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    await websocket.ping()
                    print(f"[AudioWS] Ping客户端 {client_id}", flush=True)
                except:
                    break
                    
    except websockets.exceptions.ConnectionClosed as e:
        print(f"[AudioWS] 客户端断开: {client_id}, 原因: {e}", flush=True)
    except Exception as e:
        print(f"[AudioWS] 客户端 {client_id} 错误: {e}", flush=True)
    finally:
        connected_clients.discard(websocket)
        print(f"[AudioWS] 客户端 {client_id} 已移除，当前连接数: {len(connected_clients)}", flush=True)

async def broadcast_audio_event(sound_type, count=None):
    """Broadcast audio play event to all connected clients"""
    if not connected_clients:
        print(f"[AudioWS] ⚠ 无客户端连接，跳过广播", flush=True)
        return
    
    msg_data = {
        "type": "play_audio",
        "sound": sound_type,
        "timestamp": asyncio.get_event_loop().time()
    }
    if count is not None:
        msg_data["count"] = count
        
    message = json.dumps(msg_data)
    
    print(f"[AudioWS] 广播音频事件: {sound_type} (count={count}) -> {len(connected_clients)}个客户端", flush=True)
    
    # Send to all connected clients
    disconnected = set()
    for client in connected_clients:
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosed:
            disconnected.add(client)
    
    # Clean up disconnected clients
    for client in disconnected:
        connected_clients.discard(client)

class AudioHTTPHandler(SimpleHTTPRequestHandler):
    """HTTP handler for serving audio files"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=AUDIO_DIR, **kwargs)
    
    def log_message(self, format, *args):
        print(f"[AudioHTTP] {args[0]}", flush=True)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/vnc_audio.html')
            self.end_headers()
            return
        
        # Disable caching for vnc_audio.html to ensure updates are seen
        if self.path.endswith('vnc_audio.html'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
            self.end_headers()
            
            # Serve the file content manually to ensure headers are sent
            try:
                with open(os.path.join(AUDIO_DIR, 'vnc_audio.html'), 'rb') as f:
                    self.wfile.write(f.read())
            except Exception as e:
                self.send_error(404, f"File not found: {e}")
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
