"""
name:yuval agami
date:6.1.26

"""

import socket
import os


IP = "0.0.0.0"
PORT = 80
QUEUE_SIZE = 10
SOCKET_TIMEOUT = 2

WEB_ROOT = "webroot"
DEFAULT_URL = "/index.html"

CONTENT_TYPES = {
    "html": "text/html; charset=utf-8",
    "jpg": "image/jpeg",
    "css": "text/css",
    "js": "text/javascript; charset=utf-8",
    "txt": "text/plain",
    "ico": "image/x-icon",
    "gif": "image/jpeg",
    "png": "image/png"
}




def get_file_data(file_path):
    with open(file_path, "rb") as f:
        return f.read()


def validate_http_request(request):
    try:
        lines = request.split("\r\n")
        request_line = lines[0]
        parts = request_line.split()

        if len(parts) != 3:
            return False, None

        method, resource, version = parts

        if method != "GET":
            return False, None

        if version != "HTTP/1.1":
            return False, None

        return True, resource
    except:
        return False, None


def handle_client_request(resource, client_socket):
    # ===== סטטוסים מיוחדים =====
    if resource == "/forbidden":
        response = (
            "HTTP/1.1 403 Forbidden\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            "\r\n"
            "<h1>403 Forbidden</h1>"
        )
        client_socket.send(response.encode())
        return

    if resource == "/moved":
        response = (
            "HTTP/1.1 302 Moved Temporarily\r\n"
            f"Location: {DEFAULT_URL}\r\n"
            "\r\n"
        )
        client_socket.send(response.encode())
        return

    if resource == "/error":
        response = (
            "HTTP/1.1 500 Internal Server Error\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            "\r\n"
            "<h1>500 Internal Server Error</h1>"
        )
        client_socket.send(response.encode())
        return


    if resource == "/":
        resource = DEFAULT_URL

    file_path = WEB_ROOT + resource


    if not os.path.isfile(file_path):
        response = (
            "HTTP/1.1 404 Not Found\r\n"
            "Content-Type: text/html; charset=utf-8\r\n"
            "\r\n"
            "<h1>404 Not Found</h1>"
        )
        client_socket.send(response.encode())
        return


    file_type = file_path.split(".")[-1]
    content_type = CONTENT_TYPES.get(file_type, "application/octet-stream")

    data = get_file_data(file_path)


    header = (
        "HTTP/1.1 200 OK\r\n"
        f"Content-Type: {content_type}\r\n"
        f"Content-Length: {len(data)}\r\n"
        "\r\n"
    )

    client_socket.send(header.encode() + data)


def handle_client(client_socket):
    try:
        request = client_socket.recv(1024).decode()

        if not request:
            return

        valid, resource = validate_http_request(request)

        if valid:
            handle_client_request(resource, client_socket)
        else:
            response = (
                "HTTP/1.1 400 Bad Request\r\n"
                "Content-Type: text/html; charset=utf-8\r\n"
                "\r\n"
                "<h1>400 Bad Request</h1>"
            )
            client_socket.send(response.encode())

    except:
        pass
    finally:
        client_socket.close()


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((IP, PORT))
    server_socket.listen(QUEUE_SIZE)

    print("HTTP Server running on port 80")

    while True:
        client_socket, _ = server_socket.accept()
        client_socket.settimeout(SOCKET_TIMEOUT)
        handle_client(client_socket)


if __name__ == "__main__":
    main()