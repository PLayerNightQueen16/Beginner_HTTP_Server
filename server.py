#!/usr/bin/env python3

import socket
import threading
import traceback
import json
import time
import os
from urllib.parse import urlparse, parse_qs, unquote
from email.utils import formatdate
from datetime import datetime

# CONFIG
HOST = '0.0.0.0'
PORT = 8080
MAX_REQUEST_SIZE = 1024 * 1024 * 5   # 5 MB body limit
STATIC_DIR = './static'
READ_CHUNK = 4096
KEEP_ALIVE_TIMEOUT = 15  # seconds to wait for next request on persistent connection
MAX_KEEP_ALIVE_REQUESTS = 100

# In-memory data store and lock
data_store = []
data_lock = threading.Lock()

# Simple logging
def log(msg):
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{now}][{threading.current_thread().name}] {msg}")

# Helper to format HTTP date header
def http_date():
    return formatdate(timeval=None, localtime=False, usegmt=True)

# Basic response builder
def build_response(status_code=200, reason='OK', headers=None, body=b''):
    if headers is None:
        headers = {}
    status_line = f"HTTP/1.1 {status_code} {reason}\r\n"
    # Default headers
    headers.setdefault('Date', http_date())
    headers.setdefault('Server', 'MinimalPythonHTTP/1.0')
    headers.setdefault('Content-Length', str(len(body)))
    if 'Content-Type' not in headers:
        headers['Content-Type'] = 'text/plain; charset=utf-8'
    # CORS support (bonus)
    headers.setdefault('Access-Control-Allow-Origin', '*')
    headers.setdefault('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    headers.setdefault('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    hdrs = ''.join(f"{k}: {v}\r\n" for k, v in headers.items())
    return (status_line + hdrs + "\r\n").encode('utf-8') + body

# Error helpers
def response_400(msg="Bad Request"):
    body = json.dumps({'error': msg}).encode('utf-8')
    return build_response(400, 'Bad Request', {'Content-Type': 'application/json; charset=utf-8'}, body)

def response_404(msg="Not Found"):
    body = json.dumps({'error': msg}).encode('utf-8')
    return build_response(404, 'Not Found', {'Content-Type': 'application/json; charset=utf-8'}, body)

def response_500(msg="Internal Server Error"):
    body = json.dumps({'error': msg}).encode('utf-8')
    return build_response(500, 'Internal Server Error', {'Content-Type': 'application/json; charset=utf-8'}, body)

# Parse request headers and body from a socket object (support keep-alive)
def recv_request(conn, timeout=KEEP_ALIVE_TIMEOUT):
    """
    Read bytes until full headers (CRLF CRLF) found, then parse headers and read body based on Content-Length.
    Returns: (request_line, headers_dict, body_bytes) or raises ValueError for malformed.
    """
    conn.settimeout(timeout)
    data = b''
    # Read headers
    while b'\r\n\r\n' not in data:
        try:
            chunk = conn.recv(READ_CHUNK)
        except socket.timeout:
            raise TimeoutError("Timeout while waiting for request headers")
        if not chunk:
            raise ConnectionResetError("Client closed connection while sending headers")
        data += chunk
        if len(data) > MAX_REQUEST_SIZE + 8192:
            raise ValueError("Request headers too large")
    header_part, rest = data.split(b'\r\n\r\n', 1)
    header_lines = header_part.decode('iso-8859-1').split('\r\n')
    request_line = header_lines[0]
    headers = {}
    for line in header_lines[1:]:
        if not line:
            continue
        if ':' not in line:
            continue
        k, v = line.split(':', 1)
        headers[k.strip().title()] = v.strip()
    # Body
    content_length = int(headers.get('Content-Length', '0'))
    if content_length > MAX_REQUEST_SIZE:
        raise ValueError("Request body too large")
    body = rest
    to_read = content_length - len(rest)
    while to_read > 0:
        try:
            chunk = conn.recv(min(READ_CHUNK, to_read))
        except socket.timeout:
            raise TimeoutError("Timeout while reading request body")
        if not chunk:
            raise ConnectionResetError("Client closed connection while sending body")
        body += chunk
        to_read -= len(chunk)
    return request_line, headers, body

# Route handlers
def handle_root(method, path, query, headers, body):
    if method != 'GET':
        return build_response(405, 'Method Not Allowed', {'Content-Type': 'application/json'}, json.dumps({'error':'Method Not Allowed'}).encode())
    msg = "<h1>Welcome to Minimal Python HTTP Server</h1>\n<p>Endpoints: /echo, /data, /static</p>"
    return build_response(200, 'OK', {'Content-Type': 'text/html; charset=utf-8'}, msg.encode('utf-8'))

def handle_echo(method, path, query, headers, body):
    # GET /echo?message=...
    if method != 'GET':
        return build_response(405, 'Method Not Allowed', {'Content-Type': 'application/json'}, json.dumps({'error':'Method Not Allowed'}).encode())
    message = ''
    if 'message' in query:
        message = query.get('message', [''])[0]
    response = {'message': message}
    return build_response(200, 'OK', {'Content-Type': 'application/json; charset=utf-8'}, json.dumps(response).encode('utf-8'))

def handle_post_data(method, path, query, headers, body):
    # POST /data -> accept JSON and store
    if method not in ('POST', 'PUT'):
        return build_response(405, 'Method Not Allowed', {'Content-Type': 'application/json'}, json.dumps({'error':'Method Not Allowed'}).encode())
    ct = headers.get('Content-Type', '')
    if 'application/json' not in ct:
        return build_response(400, 'Bad Request', {'Content-Type': 'application/json'}, json.dumps({'error':'Content-Type must be application/json'}).encode())
    try:
        payload = json.loads(body.decode('utf-8') if body else '{}')
    except Exception as e:
        return response_400('Invalid JSON body')
    with data_lock:
        new_id = len(data_store) + 1
        item = {'id': new_id, 'payload': payload}
        data_store.append(item)
    return build_response(201, 'Created', {'Content-Type': 'application/json; charset=utf-8'}, json.dumps({'status':'created','id':new_id}).encode('utf-8'))

def handle_get_data(method, path, query, headers, body, path_parts):
    # GET /data  OR GET /data/:id
    if method != 'GET':
        return build_response(
            405, 'Method Not Allowed',
            {'Content-Type': 'application/json'},
            json.dumps({'error': 'Method Not Allowed'}).encode()
        )

    # If /data/<id>
    if len(path_parts) == 2 and path_parts[0] == 'data':
        try:
            item_id = int(path_parts[1])
        except Exception:
            return response_400('Invalid id')

        with data_lock:
            for item in data_store:
                if item['id'] == item_id:
                    return build_response(
                        200, 'OK',
                        {'Content-Type': 'application/json; charset=utf-8'},
                        json.dumps(item).encode('utf-8')
                    )

        return response_404('Item not found')

    # Else return all
    with data_lock:
        return build_response(
            200, 'OK',
            {'Content-Type': 'application/json; charset=utf-8'},
            json.dumps(data_store).encode('utf-8')
        )


def handle_delete_data(method, path, query, headers, body, path_parts):
    if method != 'DELETE':
        return build_response(
            405, 'Method Not Allowed',
            {'Content-Type': 'application/json'},
            json.dumps({'error': 'Method Not Allowed'}).encode()
        )

    # If /data/<id>
    if len(path_parts) == 2 and path_parts[0] == 'data':
        try:
            item_id = int(path_parts[1])
        except Exception:
            return response_400('Invalid id')

        with data_lock:
            for i, item in enumerate(data_store):
                if item['id'] == item_id:
                    data_store.pop(i)
                    return build_response(
                        200, 'OK',
                        {'Content-Type': 'application/json; charset=utf-8'},
                        json.dumps({'status': 'deleted'}).encode('utf-8')
                    )

        return response_404('Item not found')

    return response_400('No id provided')

def handle_static(method, subpath):
    # Serve files under STATIC_DIR
    if method != 'GET':
        return build_response(405, 'Method Not Allowed', {'Content-Type': 'application/json'}, json.dumps({'error':'Method Not Allowed'}).encode())
    # Prevent path traversal
    safe_path = os.path.normpath(unquote(subpath)).lstrip(os.sep)
    full_path = os.path.join(STATIC_DIR, safe_path)
    if not os.path.isfile(full_path):
        return response_404('Static file not found')
    try:
        with open(full_path, 'rb') as f:
            content = f.read()
        # simple content-type detection
        if full_path.endswith('.html'):
            ctype = 'text/html; charset=utf-8'
        elif full_path.endswith('.css'):
            ctype = 'text/css; charset=utf-8'
        elif full_path.endswith('.js'):
            ctype = 'application/javascript; charset=utf-8'
        else:
            ctype = 'application/octet-stream'
        return build_response(200, 'OK', {'Content-Type': ctype}, content)
    except Exception as e:
        log("Error reading static file: " + str(e))
        return response_500('Error reading static file')

# Main dispatcher
def dispatch_request(method, path, headers, body):
    parsed = urlparse(path)
    path_only = parsed.path
    query = parse_qs(parsed.query)
    path_parts = [p for p in path_only.split('/') if p != '']
    try:
        # Root
        if path_only == '/':
            return handle_root(method, path_only, query, headers, body)
        # Echo
        if path_only.startswith('/echo'):
            return handle_echo(method, path_only, query, headers, body)
        # Static files: /static/...
        if path_only.startswith('/static/'):
            subpath = path_only[len('/static/'):]
            return handle_static(method, subpath)
        # POST /data or PUT /data
        if path_only == '/data' and method in ('POST','PUT'):
            return handle_post_data(method, path_only, query, headers, body)
        # GET /data or GET /data/:id
        if path_parts and path_parts[0] == 'data':
            if method == 'GET':
                # pass path_parts to retrieve id
                return handle_get_data(method, path_only, query, headers, body, path_parts)
            elif method == 'DELETE':
                return handle_delete_data(method, path_only, query, headers, body, path_parts)
            elif method in ('POST','PUT'):  # fallback already handled
                return handle_post_data(method, path_only, query, headers, body)
        # Not found
        return response_404('Route not found')
    except Exception as e:
        log("Exception in dispatcher: " + repr(e))
        traceback.print_exc()
        return response_500('Unhandled server error')

# Client handler thread
def handle_client(conn, addr):
    conn.settimeout(KEEP_ALIVE_TIMEOUT)
    try:
        keep_alive_requests = 0

        while True:
            # Read request
            try:
                request_line, headers, body = recv_request(conn)

            except TimeoutError:
                # Idle keep-alive timeout — close quietly
                log(f"Idle timeout, closing connection from {addr}")
                break

            except ConnectionResetError:
                # Client closed connection abruptly
                break

            except ValueError as e:
                # Malformed request (too large headers/body, bad format, etc.)
                log(f"Bad request from {addr}: {e}")
                try:
                    conn.sendall(response_400(str(e)))
                except Exception:
                    pass
                break

            except Exception as e:
                # Unexpected server error
                log(f"Unexpected error receiving request: {e}")
                try:
                    conn.sendall(response_500('Error reading request'))
                except Exception:
                    pass
                break

            # Parse Request
            try:
                parts = request_line.split()
                method   = parts[0].upper()
                path     = parts[1]
                version  = parts[2] if len(parts) > 2 else 'HTTP/1.1'
            except Exception:
                # Malformed request line -> inform client and close
                try:
                    conn.sendall(response_400('Malformed request line'))
                except Exception:
                    pass
                break

            # Log request
            log(f"{addr} \"{method} {path} {version}\" Headers:{len(headers)} BodyLen:{len(body)}")

            # Handle Options
            if method == 'OPTIONS':
                resp = build_response(
                    204, 'No Content',
                    {'Content-Type': 'text/plain'},
                    b''
                )
                try:
                    conn.sendall(resp)
                except Exception:
                    pass
            else:
                # Dispatch Route
                try:
                    resp = dispatch_request(method, path, headers, body)
                except Exception as e:
                    log(f"Error dispatching request: {e}")
                    resp = response_500('Dispatcher error')

                try:
                    conn.sendall(resp)
                except BrokenPipeError:
                    log("Client disconnected during send")
                    break
                except Exception:
                    # other send errors -> close connection
                    break

            # Keep-Alive
            connection_header = headers.get('Connection', '').lower()
            keep_alive = True

            # HTTP/1.0 does NOT keep connections alive unless specified
            if version == 'HTTP/1.0' and connection_header != 'keep-alive':
                keep_alive = False

            # Client explicitly requests connection close
            if connection_header == 'close':
                keep_alive = False

            keep_alive_requests += 1

            # Limit max number of requests per connection
            if keep_alive_requests >= MAX_KEEP_ALIVE_REQUESTS:
                keep_alive = False

            # If we are NOT keeping alive, break here
            if not keep_alive:
                break

    finally:
        try:
            conn.close()
        except:
            pass
        log(f"Connection {addr} closed")

def run_server(host=HOST, port=PORT):
    log(f"Starting server on {host}:{port}")
    if not os.path.isdir(STATIC_DIR):
        os.makedirs(STATIC_DIR, exist_ok=True)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(128)
    try:
        while True:
            conn, addr = srv.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            t.start()
    except KeyboardInterrupt:
        log("Shutting down server (keyboard interrupt)")
    finally:
        srv.close()

if __name__ == '__main__':
    run_server()
