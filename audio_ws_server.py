#!/usr/bin/env python3
"""
WebSocket Audio Server for Browser Audio Playback
- HTTP: serves login/setup and static resources (vnc_audio.html, assets)
- WS: broadcasts audio play events to connected browsers
"""

import asyncio
import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
import time
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

import websockets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
AUDIO_DIR = BASE_DIR

AUTH_FILE = os.path.join(DATA_DIR, "auth.json")
AUDIO_HTTP_PORT = int(os.environ.get("AUDIO_HTTP_PORT", "8080"))
AUDIO_WS_PORT = int(os.environ.get("AUDIO_WS_PORT", "8765"))
INTERNAL_EVENT_PORT = int(os.environ.get("AUDIO_EVENT_PORT", "8865"))
SESSION_COOKIE_NAME = "goodgym_session"
SESSION_TTL_SECONDS = int(os.environ.get("SESSION_TTL_SECONDS", "43200"))

_SESSIONS = {}
_CONNECTED_CLIENTS = set()
event_loop = None


def _hash_password(password, salt_bytes):
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt_bytes, 120000)
    return base64.b64encode(digest).decode("ascii")


def load_auth():
    if not os.path.exists(AUTH_FILE):
        return None
    try:
        with open(AUTH_FILE, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
        if isinstance(data, dict) and data.get("username"):
            return data
    except Exception:
        return None
    return None


def save_auth(username, password):
    os.makedirs(os.path.dirname(AUTH_FILE), exist_ok=True)
    salt = secrets.token_bytes(16)
    data = {
        "username": username,
        "salt": base64.b64encode(salt).decode("ascii"),
        "password_hash": _hash_password(password, salt),
    }
    with open(AUTH_FILE, "w", encoding="utf-8") as file_handle:
        json.dump(data, file_handle)


def verify_credentials(auth_data, username, password):
    if not auth_data or not username or not password:
        return False
    if username != auth_data.get("username"):
        return False

    if auth_data.get("password_hash") and auth_data.get("salt"):
        try:
            salt = base64.b64decode(auth_data["salt"])
        except Exception:
            return False
        expected = auth_data["password_hash"]
        actual = _hash_password(password, salt)
        return hmac.compare_digest(actual, expected)

    plain_password = auth_data.get("password", "")
    if hmac.compare_digest(password, plain_password):
        save_auth(username, password)
        return True
    return False


def _create_session(username):
    token = secrets.token_urlsafe(32)
    _SESSIONS[token] = {
        "username": username,
        "expires_at": time.time() + SESSION_TTL_SECONDS,
    }
    return token


def _get_session(token):
    if not token:
        return None
    session = _SESSIONS.get(token)
    if not session:
        return None
    if session["expires_at"] < time.time():
        _SESSIONS.pop(token, None)
        return None
    return session


def _parse_cookies(cookie_header):
    cookies = {}
    if not cookie_header:
        return cookies
    for part in cookie_header.split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        cookies[key.strip()] = value.strip()
    return cookies


def _get_cookie_header(headers):
    if not headers:
        return ""
    cookie_value = headers.get("Cookie")
    if cookie_value is None:
        cookie_value = headers.get("cookie")
    return cookie_value or ""


def _get_ws_headers(websocket):
    headers = getattr(websocket, "request_headers", None)
    if headers:
        return headers
    request = getattr(websocket, "request", None)
    if request and hasattr(request, "headers"):
        return request.headers
    return {}


def _get_ws_path(websocket, path=None):
    if path:
        return path
    if hasattr(websocket, "path"):
        return websocket.path
    request = getattr(websocket, "request", None)
    if request and hasattr(request, "path"):
        return request.path
    return None


def _get_session_from_headers(headers):
    cookies = _parse_cookies(_get_cookie_header(headers))
    return _get_session(cookies.get(SESSION_COOKIE_NAME))


def _get_session_from_request(headers, path):
    session = _get_session_from_headers(headers)
    if session:
        return session
    if not path:
        return None
    try:
        parsed = urllib.parse.urlparse(path)
        params = urllib.parse.parse_qs(parsed.query)
        token = params.get("token", [None])[0]
    except Exception:
        token = None
    return _get_session(token)


def get_setup_page(error=None):
    error_html = f'<div style="color:red;margin-bottom:10px;">{error}</div>' if error else ""
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
""".encode("utf-8")


def get_login_page(error=None, username=""):
    error_html = f'<div style="color:red;margin-bottom:10px;">{error}</div>' if error else ""
    username_value = username or "admin"
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Good-GYM Login</title>
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
        <h2>🔐 Good-GYM 登录</h2>
        <p style="text-align:center;color:#718096;margin-bottom:1.5rem;">请输入账号密码以进入主界面</p>
        {error_html}
        <form method="POST" action="/login">
            <label>用户名</label>
            <input type="text" name="username" value="{username_value}" required>
            <label>密码</label>
            <input type="password" name="password" required placeholder="请输入密码">
            <button type="submit">登录</button>
        </form>
    </div>
</body>
</html>
""".encode("utf-8")


class AudioHTTPHandler(SimpleHTTPRequestHandler):
    """HTTP handler for login/setup and static resources"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=AUDIO_DIR, **kwargs)

    def log_message(self, format, *args):
        pass

    def _send_html(self, payload):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _redirect(self, location):
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

    def _set_session_cookie(self, token):
        cookie = f"{SESSION_COOKIE_NAME}={token}; Path=/; HttpOnly; SameSite=Strict"
        self.send_header("Set-Cookie", cookie)

    def _clear_session_cookie(self):
        cookie = f"{SESSION_COOKIE_NAME}=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict"
        self.send_header("Set-Cookie", cookie)

    def _get_session(self):
        return _get_session_from_headers(self.headers)

    def _should_allow_path(self, path):
        return path == "/vnc_audio.html" or path.startswith("/assets/")

    def list_directory(self, path):
        self.send_error(404)
        return None

    def do_POST(self):
        auth_data = load_auth()
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if not auth_data:
            if path != "/setup":
                self.send_error(405)
                return

            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                post_data = self.rfile.read(content_length).decode("utf-8")
                params = urllib.parse.parse_qs(post_data)

                user = params.get("username", ["admin"])[0].strip()
                pwd = params.get("password", [""])[0]

                if user and pwd:
                    save_auth(user, pwd)
                    self._redirect("/login")
                    return
            except Exception as exc:
                print(f"[Auth] Setup error: {exc}", flush=True)

            self._send_html(get_setup_page("无效的请求"))
            return

        if path == "/login":
            user = ""
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                post_data = self.rfile.read(content_length).decode("utf-8")
                params = urllib.parse.parse_qs(post_data)

                user = params.get("username", [""])[0].strip()
                pwd = params.get("password", [""])[0]

                if verify_credentials(auth_data, user, pwd):
                    token = _create_session(user)
                    self.send_response(302)
                    self._set_session_cookie(token)
                    self.send_header("Location", "/")
                    self.end_headers()
                    return
            except Exception as exc:
                print(f"[Auth] Login error: {exc}", flush=True)

            self._send_html(get_login_page("账号或密码错误", username=user))
            return

        self.send_error(405)

    def do_GET(self):
        auth_data = load_auth()
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path

        if not auth_data:
            if path == "/setup":
                self._send_html(get_setup_page())
                return
            self._redirect("/setup")
            return

        if path == "/setup":
            self._redirect("/login")
            return

        if path == "/login":
            session = self._get_session()
            if session:
                self._redirect("/")
                return
            self._send_html(get_login_page(username=auth_data.get("username", "")))
            return

        if path == "/logout":
            self.send_response(302)
            self._clear_session_cookie()
            self.send_header("Location", "/login")
            self.end_headers()
            return

        session = self._get_session()
        if not session:
            if path == "/" or path == "/vnc_audio.html":
                self._redirect("/login")
            else:
                self.send_error(401, "Authentication required")
            return

        if path == "/ws_token":
            cookies = _parse_cookies(self.headers.get("Cookie", ""))
            token = cookies.get(SESSION_COOKIE_NAME)
            if not token or not _get_session(token):
                self.send_error(401, "Authentication required")
                return
            payload = json.dumps({"token": token}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)
            return

        if path == "/":
            self._redirect("/vnc_audio.html")
            return

        if path == "/vnc_audio.html":
            try:
                with open(os.path.join(AUDIO_DIR, "vnc_audio.html"), "rb") as file_handle:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(file_handle.read())
                return
            except Exception as exc:
                print(f"[AudioHTTP] Failed to load vnc_audio.html: {exc}", flush=True)
                self.send_error(500)
                return

        if not self._should_allow_path(path):
            self.send_error(404)
            return

        super().do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()


def run_http_server():
    try:
        server = HTTPServer(("0.0.0.0", AUDIO_HTTP_PORT), AudioHTTPHandler)
        print(f"[AudioHTTP] OK HTTP服务器启动在端口 {AUDIO_HTTP_PORT}", flush=True)
        server.serve_forever()
    except Exception as exc:
        print(f"[AudioHTTP] ERR HTTP服务器启动失败: {exc}", flush=True)


def _is_ws_authenticated(headers, path):
    session = _get_session_from_request(headers, path)
    if session:
        return True
    try:
        parsed = urllib.parse.urlparse(path or "")
        safe_path = parsed.path or "/"
        params = urllib.parse.parse_qs(parsed.query)
        token_present = bool(params.get("token"))
    except Exception:
        safe_path = "/"
        token_present = False
    cookies = _parse_cookies(_get_cookie_header(headers))
    cookie_present = SESSION_COOKIE_NAME in cookies
    print(
        f"[AudioWS] WARN 未授权: path={safe_path}, cookie_present={cookie_present}, token_present={token_present}",
        flush=True,
    )
    return False


async def handle_client(websocket, _path=None):
    try:
        headers = _get_ws_headers(websocket)
        path = _get_ws_path(websocket, _path)
        if not _is_ws_authenticated(headers, path):
            print("[AudioWS] WARN 未授权的WebSocket连接被拒绝", flush=True)
            await websocket.close(code=4401, reason="Unauthorized")
            return

        _CONNECTED_CLIENTS.add(websocket)
        print(f"[AudioWS] OK 客户端已连接: {websocket.remote_address}", flush=True)
        await websocket.send(json.dumps({"type": "connected", "message": "ok"}))
        async for _message in websocket:
            pass
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as exc:
        print(f"[AudioWS] ERR 处理异常: {exc}", flush=True)
        import traceback

        traceback.print_exc()
        try:
            await websocket.close(code=1011, reason="Server error")
        except Exception:
            pass
    finally:
        close_code = getattr(websocket, "close_code", None)
        close_reason = getattr(websocket, "close_reason", None)
        print(
            f"[AudioWS] WARN 客户端已断开: {websocket.remote_address}, code={close_code}, reason={close_reason}",
            flush=True,
        )
        _CONNECTED_CLIENTS.discard(websocket)


async def broadcast_audio_event(sound_type, count):
    if not _CONNECTED_CLIENTS:
        print("[AudioWS] WARN 无在线客户端，跳过音频广播", flush=True)
        return
    payload = {"type": "play_audio", "sound": sound_type}
    if count is not None:
        payload["count"] = count
    message = json.dumps(payload)
    print(f"[AudioWS] OK 广播音频事件: {sound_type}, count={count}, clients={len(_CONNECTED_CLIENTS)}", flush=True)

    stale_clients = []
    for client in _CONNECTED_CLIENTS:
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosed:
            stale_clients.append(client)
    for client in stale_clients:
        _CONNECTED_CLIENTS.discard(client)


def run_event_listener():
    global event_loop

    import socket

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind(("127.0.0.1", INTERNAL_EVENT_PORT))
        server_socket.listen(5)
        print(f"[AudioEvent] OK 内部事件监听器启动在端口 {INTERNAL_EVENT_PORT}", flush=True)

        while True:
            try:
                client_socket, _addr = server_socket.accept()
                data = client_socket.recv(1024).decode("utf-8", errors="ignore")
                client_socket.close()

                if not data:
                    continue
                print(f"[AudioEvent] 收到事件: {data}", flush=True)
                try:
                    event_data = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if event_data.get("type") != "play_audio":
                    continue
                sound_type = event_data.get("sound", "count")
                count = event_data.get("count")
                if event_loop:
                    asyncio.run_coroutine_threadsafe(
                        broadcast_audio_event(sound_type, count),
                        event_loop,
                    )
            except Exception as exc:
                print(f"[AudioEvent] 处理错误: {exc}", flush=True)

    except Exception as exc:
        print(f"[AudioEvent] ERR 监听器启动失败: {exc}", flush=True)


async def main():
    global event_loop

    event_loop = asyncio.get_running_loop()

    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    event_thread = threading.Thread(target=run_event_listener, daemon=True)
    event_thread.start()

    print(f"[AudioWS] OK WebSocket服务器启动在端口 {AUDIO_WS_PORT}", flush=True)

    async with websockets.serve(handle_client, "0.0.0.0", AUDIO_WS_PORT):
        print(f"[AudioWS] ========== 服务器就绪 ==========", flush=True)
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[AudioWS] 服务器关闭", flush=True)
    except Exception as exc:
        print(f"[AudioWS] ERR 服务器错误: {exc}", flush=True)
        import traceback

        traceback.print_exc()
