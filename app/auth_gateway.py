#!/usr/bin/env python3
import socket
import threading
import select
import base64
import json
import os
import urllib.parse

# Configuration
LISTEN_PORT = 6080
TARGET_HOST = 'localhost'
TARGET_PORT = 6081
AUTH_FILE = '/app/data/auth.json'

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
    # Ensure directory exists
    os.makedirs(os.path.dirname(AUTH_FILE), exist_ok=True)
    with open(AUTH_FILE, 'w') as f:
        json.dump(data, f)

def get_setup_page(error=None):
    error_html = f'<div style="color:red;margin-bottom:10px;">{error}</div>' if error else ''
    return f"""HTTP/1.1 200 OK
Content-Type: text/html
Connection: close

<!DOCTYPE html>
<html>
<head>
    <title>Good-GYM Setup</title>
    <style>
        body {{ font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f0f2f5; }}
        .card {{ background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); width: 300px; }}
        input {{ width: 100%; padding: 8px; margin: 8px 0; box-sizing: border-box; border: 1px solid #ddd; border-radius: 4px; }}
        button {{ width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }}
        button:hover {{ background: #0056b3; }}
        h2 {{ text-align: center; color: #333; }}
    </style>
</head>
<body>
    <div class="card">
        <h2>Good-GYM Setup</h2>
        <p>Please set up your access credentials.</p>
        {error_html}
        <form method="POST" action="/setup">
            <label>Username (default: admin)</label>
            <input type="text" name="username" value="admin" required>
            <label>Password</label>
            <input type="password" name="password" required>
            <button type="submit">Set Credentials</button>
        </form>
    </div>
</body>
</html>
""".encode('utf-8')

def proxy_connection(client_socket, target_socket, initial_data):
    try:
        target_socket.sendall(initial_data)
        
        sockets = [client_socket, target_socket]
        while True:
            readable, _, _ = select.select(sockets, [], [], 60)
            if not readable:
                break
            for s in readable:
                data = s.recv(4096)
                if not data:
                    return
                if s is client_socket:
                    target_socket.sendall(data)
                else:
                    client_socket.sendall(data)
    except Exception:
        pass
    finally:
        client_socket.close()
        target_socket.close()

def handle_client(client_socket):
    try:
        # Read initial request headers
        data = client_socket.recv(4096)
        if not data:
            client_socket.close()
            return

        auth_data = load_auth()
        
        # Parse minimal info from headers
        request_str = data.decode('utf-8', errors='ignore')
        first_line = request_str.split('\r\n')[0]
        method, path, _ = first_line.split(' ') if len(first_line.split(' ')) >= 2 else ('', '', '')

        # 1. SETUP FLOW: If no auth defined
        if not auth_data:
            if method == 'POST' and path == '/setup':
                # Handle POST: Extract body
                try:
                    headers, body = request_str.split('\r\n\r\n', 1)
                    # Very basic URL encoded parsing
                    params = urllib.parse.parse_qs(body)
                    user = params.get('username', ['admin'])[0]
                    pwd = params.get('password', [''])[0]
                    
                    if user and pwd:
                        save_auth(user, pwd)
                        # Redirect to root
                        response = "HTTP/1.1 302 Found\r\nLocation: /\r\nConnection: close\r\n\r\n".encode('utf-8')
                        client_socket.sendall(response)
                        return
                except:
                    pass
                # On failure or weird post, show setup again
                client_socket.sendall(get_setup_page("Invalid request"))
                return
            else:
                # Show Setup Page for any other request
                client_socket.sendall(get_setup_page())
                return

        # 2. AUTH FLOW: Check Basic Auth
        is_authenticated = False
        target_header = f"Authorization: Basic {base64.b64encode(f'{auth_data['username']}:{auth_data['password']}'.encode()).decode()}"
        
        # Case-insensitive header check
        headers_connect = request_str.split('\r\n\r\n')[0]
        for line in headers_connect.split('\r\n'):
            if line.lower().startswith("authorization:") and target_header in line:
                is_authenticated = True
                break
        
        if is_authenticated:
            # PROXY to Real Server
            try:
                target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                target_socket.connect((TARGET_HOST, TARGET_PORT))
                proxy_connection(client_socket, target_socket, data)
            except Exception as e:
                print(f"Proxy connection failed: {e}")
                client_socket.close()
        else:
            # 401 Challenge
            response = 'HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: Basic realm="Good-GYM Login"\r\nContent-Length: 0\r\nConnection: close\r\n\r\n'.encode('utf-8')
            client_socket.sendall(response)
            client_socket.close()

    except Exception as e:
        print(f"Handler error: {e}")
        client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # Retry binding if address in use (e.g. if container restart is slow)
    import time
    for i in range(5):
        try:
            server.bind(('0.0.0.0', LISTEN_PORT))
            break
        except OSError:
            print(f"Port {LISTEN_PORT} busy, retrying...")
            time.sleep(2)
            
    server.listen(100)
    print(f"Auth Gateway listening on port {LISTEN_PORT} -> {TARGET_HOST}:{TARGET_PORT}")
    print(f"Auth Config: {AUTH_FILE}")

    while True:
        client, addr = server.accept()
        t = threading.Thread(target=handle_client, args=(client,))
        t.daemon = True
        t.start()

if __name__ == '__main__':
    main()
