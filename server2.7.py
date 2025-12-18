

import socket
import os
import glob
import shutil
import subprocess
import pyautogui
from protocol import Protocol

IP = "0.0.0.0"
PORT = 6767
QUEUE = 1
SCREENSHOT_PATH = "screenshot.jpg"

#recives the directory and returns the files inside the folder
def dir_cmd(folder):
    files = glob.glob(folder + "/*")
    return "|".join(files)

#recives the file path to delete and returns ok if the file was deleted
def delete(path):
    try:
        os.remove(path)
        return "OK"
    except:
        return "ERROR"

#recives the path of the file to copy and the destination path and returns ok if the file was copied
def copy_cmd(src, dst):
    try:
        shutil.copy(src, dst)
        return "OK"
    except:
        return "ERROR"

#recive a string command to run using the operating system returns ok if the command was executed
#whitout throwing an exception
def execute(exe):
    try:
        subprocess.call(exe)
        return "OK"
    except:
        return "ERROR"

#recives nothing and returns ok if the screenshot captured and saved or error if it didnt
def take_screenshot():
    try:
        img = pyautogui.screenshot()
        img.save(SCREENSHOT_PATH)
        os.startfile(SCREENSHOT_PATH)
        return "OK"
    except:
        return "ERROR"

#resives nothing and returns the binary bytes of the screenshot file
def send_screenshot():
    try:
        with open(SCREENSHOT_PATH, "rb") as f:
            return f.read()
    except:
        return "ERROR"

#recives the command sent by the client and returns an answer accordingly
def get_answer(cmd):
    if not cmd.strip():
        return "invalid"
    parts = cmd.split()
    op = parts[0].upper()

    if op == "DIR":
        return dir_cmd(parts[1])

    elif op == "DELETE":
        return delete(parts[1])

    elif op == "COPY":
        return copy_cmd(parts[1], parts[2])

    elif op == "EXECUTE":
        return execute(parts[1])

    elif op == "TAKE_SCREENSHOT":
        return take_screenshot()

    elif op == "SEND_SCREENSHOT":
        return send_screenshot()  # מחזיר bytes

    elif op == "EXIT":
        return "bye"
    else:
        return "invalid"

def main():
    server = socket.socket()
    server.bind((IP, PORT))
    server.listen(QUEUE)

    print("Server ready")

    while True:
        client, addr = server.accept()
        print("Client connected:", addr)
        try:
            while True:
                cmd_bytes = Protocol.recv_with_length(client)
                if not cmd_bytes:
                    print("Client disconnected")
                    break
                cmd = cmd_bytes.decode()
                ans = get_answer(cmd)
                Protocol.send_with_length(client, ans)


        except socket.error as msg:
            print("Server socket error:", msg)

        finally:
            # תמיד יסגר את הסוקט של הקליינט
            client.close()
            print("Client disconnected")


if __name__ == "__main__":
    main()

