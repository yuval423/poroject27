import struct

class Protocol:
    LEN_SIGN = "!I"       # 4 bytes
    LENGTH_SIZE = 4
#recives socket and data (string or bytes) and sends a length prefixed messege to client
    @staticmethod
    def send_with_length(sock, data):
        if isinstance(data, str):
            data = data.encode()

        header = struct.pack(Protocol.LEN_SIGN, len(data))
        sock.sendall(header + data)

#recives socket returns the bytes rfrom the socket
    @staticmethod
    def recv_with_length(sock):
        header = sock.recv(Protocol.LENGTH_SIZE)
        if not header:
            return None

        (length,) = struct.unpack(Protocol.LEN_SIGN, header)
        if length == 0:
            return b""

        data = b""
        while len(data) < length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                return None
            data += chunk

        return data