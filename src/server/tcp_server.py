import socket
import threading
from common.net_utils import recv_exact
from common.constants import request_len

def run_tcp_server(bind_ip: str, bind_port: int, handle_client_fn):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((bind_ip, bind_port))
    s.listen()

    actual_port = s.getsockname()[1]

    def accept_loop():
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_client_fn, args=(conn, addr), daemon=True)
            t.start()

    t = threading.Thread(target=accept_loop, daemon=True)
    t.start()
    return actual_port