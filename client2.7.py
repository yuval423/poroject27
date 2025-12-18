"""
author - yuval agami
date   - 5.12.25
"""
import socket
from protocol import Protocol

SERVER_IP = "127.0.0.1"
SERVER_PORT = 6767


def main():
    sock = socket.socket()
    sock.connect((SERVER_IP, SERVER_PORT))

    print("Connected to server")

    while True:
        cmd = input("Enter command: ")

        # שולח פקודה
        Protocol.send_with_length(sock, cmd)

        # מקבל תשובה
        ans = Protocol.recv_with_length(sock)

        # אם קיבלנו "bye" סוקט נסגר
        if ans == b"bye":
            print("bye")
            print("Server closed connection")
            break

        # screenshot מגיע כ-bytes
        if cmd.upper() == "SEND_SCREENSHOT":
            with open("received_screenshot.jpg", "wb") as f:
                f.write(ans)
            print("Screenshot saved as received_screenshot.jpg")
        else:
            print("Server:", ans.decode())


    sock.close()


if __name__ == "__main__":
    main()