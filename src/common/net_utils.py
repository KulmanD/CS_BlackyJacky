import socket

def recv_exact(sock: socket.socket, n: int) -> bytes:
    # recv until we have exactly n bytes or the peer disconnects
    chunks = []
    got = 0
    while got < n:
        part = sock.recv(n - got)
        if part == b"":
            raise ConnectionError("peer disconnected")
        chunks.append(part)
        got += len(part)
    return b"".join(chunks)

def pad_name(s: str, length: int) -> bytes:
    # ascii name, trimmed and padded with zeros
    b = s.encode("ascii", errors="ignore")[:length]
    return b + b"\x00" * (length - len(b))

def read_name(b: bytes) -> str:
    # stop at first null byte
    return b.split(b"\x00", 1)[0].decode("ascii", errors="ignore")