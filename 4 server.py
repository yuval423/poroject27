"""
name:yuval agami
date:12.3.26
"""

import socket
import os
import logging
from urllib.parse import urlparse, parse_qs

# --- Constants and Configuration ---
IP = '0.0.0.0'
PORT = 80
QUEUE_SIZE = 10
SOCKET_TIMEOUT = 5.0
BUFFER_SIZE = 8192
WEB_ROOT = "webroot"
UPLOAD_DIR = os.path.join(WEB_ROOT, "uploads")
IMAGES_DIR = os.path.join(WEB_ROOT, "imgs")
DEFAULT_URL = "/index.html"
LOG_FILE = "server.log"

# --- Resource Paths ---
IMG_PATH = '/image'
CALC_NEXT_PATH = '/calculate-next'
CALC_AREA_PATH = '/calculate-area'
UPLOAD_PATH = '/upload'

# --- Content Types ---
CONTENT_TYPES = {
    "html": "text/html;charset=utf-8",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "css": "text/css",
    "js": "text/javascript; charset=UTF-8",
    "txt": "text/plain",
    "ico": "image/x-icon",
    "gif": "image/gif",
    "png": "image/png"
}

# --- Special Paths and Responses ---
REDIRECTION_DICTIONARY = {"/moved": "/"}
FORBIDDEN_LIST = ["/forbidden"]
ERROR_LIST = ["/error"]

RESPONSE_200_HEADER = "HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {length}\r\n\r\n"
RESPONSE_302 = "HTTP/1.1 302 Moved Temporarily\r\nLocation: {location}\r\n\r\n"
RESPONSE_400 = b"HTTP/1.1 400 Bad Request\r\n\r\n"
RESPONSE_403 = b"HTTP/1.1 403 Forbidden\r\n\r\n"
RESPONSE_404 = b"HTTP/1.1 404 Not Found\r\n\r\n"
RESPONSE_500 = b"HTTP/1.1 500 Internal Server Error\r\n\r\n"

logger = logging.getLogger(__name__)

def validate_environment():

    if not (0 < PORT < 65536):
        exit(1)
    for directory in [WEB_ROOT, IMAGES_DIR, UPLOAD_DIR]:
        if not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)

def get_file_data(file_name):

    if os.path.isfile(file_name):
        try:
            with open(file_name, 'rb') as f:
                return f.read()
        except IOError:
            logger.error(f"Error reading file: {file_name}")
            raise
    return None

def handle_post_request(resource, body, client_socket):

    parsed_url = urlparse(resource)
    params = parse_qs(parsed_url.query)

    if parsed_url.path == UPLOAD_PATH:
        file_name = params.get('file-name', ['uploaded_file'])[0]
        file_path = os.path.join(UPLOAD_DIR, file_name)
        try:
            with open(file_path, 'wb') as f:
                f.write(body)
            logger.info(f"File uploaded: {file_name}")
            response = "HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nOK"
            client_socket.send(response.encode())
        except Exception as e:
            logger.error(f"Upload error: {e}")
            client_socket.send(RESPONSE_500)

def handle_get_request(resource, client_socket):

    parsed_url = urlparse(resource)
    uri = parsed_url.path
    params = parse_qs(parsed_url.query)

    if uri == '/': uri = DEFAULT_URL

    # Status Handlers
    if uri in REDIRECTION_DICTIONARY:
        client_socket.send(RESPONSE_302.format(location=REDIRECTION_DICTIONARY[uri]).encode())
        return
    if uri in FORBIDDEN_LIST:
        client_socket.send(RESPONSE_403); return
    if uri in ERROR_LIST:
        client_socket.send(RESPONSE_500); return

    # Dynamic: Image
    if uri == IMG_PATH:
        img_name = params.get('image-name', [''])[0]
        # Check static imgs first, then uploads
        data = get_file_data(os.path.join(IMAGES_DIR, img_name))
        if data is None:
            data = get_file_data(os.path.join(UPLOAD_DIR, img_name))

        if data:
            ext = img_name.split('.')[-1].lower()
            header = RESPONSE_200_HEADER.format(content_type=CONTENT_TYPES.get(ext, "image/jpeg"), length=len(data))
            client_socket.send(header.encode() + data)
        else:
            client_socket.send(RESPONSE_404)
        return

    # Dynamic: Calculator Next
    if uri == CALC_NEXT_PATH:
        num = params.get('num', ['0'])[0]
        result = str(int(num) + 1) if num.isdigit() else "Error"
        header = RESPONSE_200_HEADER.format(content_type="text/plain", length=len(result))
        client_socket.send(header.encode() + result.encode())
        return

    # Dynamic: Calculator Area (Triangle)
    if uri == CALC_AREA_PATH:
        try:
            h = int(params.get('height', ['0'])[0])
            w = int(params.get('width', ['0'])[0])
            area = str(h * w / 2)
            header = RESPONSE_200_HEADER.format(content_type="text/plain", length=len(area))
            client_socket.send(header.encode() + area.encode())
        except (ValueError, TypeError):
            client_socket.send(RESPONSE_400)
        return

    # Static Files
    file_path = os.path.join(WEB_ROOT, uri.strip("/"))
    try:
        data = get_file_data(file_path)
        if data is not None:
            ext = uri.split('.')[-1].lower()
            header = RESPONSE_200_HEADER.format(content_type=CONTENT_TYPES.get(ext, "text/plain"), length=len(data))
            client_socket.send(header.encode() + data)
        else:
            client_socket.send(RESPONSE_404)
    except IOError:
        client_socket.send(RESPONSE_500)

def handle_client(client_socket):

    leftover_data = b""
    try:
        while True:
            raw_data = client_socket.recv(BUFFER_SIZE)
            if not raw_data: break

            data = leftover_data + raw_data
            header_end = data.find(b'\r\n\r\n')
            if header_end == -1:
                leftover_data = data
                continue

            header_text = data[:header_end].decode('utf-8', errors='ignore')
            content_start = header_end + 4

            # Content Length parse
            content_length = 0
            for line in header_text.split('\r\n'):
                if line.lower().startswith('content-length:'):
                    content_length = int(line.split(':')[1].strip())

            # Read remaining body if not fully in buffer
            body_already_read = data[content_start:]
            while len(body_already_read) < content_length:
                more_body = client_socket.recv(BUFFER_SIZE)
                if not more_body: break
                body_already_read += more_body

            current_body = body_already_read[:content_length]
            leftover_data = body_already_read[content_length:] # Keep for next request

            request_line = header_text.split('\r\n')[0].split()
            if len(request_line) < 2: break

            method, resource = request_line[0], request_line[1]
            if method == 'GET':
                handle_get_request(resource, client_socket)
            elif method == 'POST':
                handle_post_request(resource, current_body, client_socket)
            else:
                client_socket.send(RESPONSE_400); break

    except (socket.timeout, socket.error): pass
    finally: client_socket.close()

def main():
    validate_environment()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((IP, PORT))
        server_socket.listen(QUEUE_SIZE)
        print(f"Server is up on port {PORT}")
        while True:
            client_conn, addr = server_socket.accept()
            client_conn.settimeout(SOCKET_TIMEOUT)
            handle_client(client_conn)
    finally: server_socket.close()

if __name__ == "__main__":
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
    main()