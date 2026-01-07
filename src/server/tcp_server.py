import socket
import threading


def run_tcp_server(bind_ip: str, bind_port: int, handle_client_fn):
    # create tcp server socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # bind + listen
    s.bind((bind_ip, bind_port))
    s.listen()

    # actual port (if bind_port = 0)
    actual_port = s.getsockname()[1]

    def accept_loop():
        while True:
            try:
                conn, addr = s.accept()
            except OSError:
                # socket closed -> stop thread
                break

            # handle each client in its own thread
            t = threading.Thread(
                target=handle_client_fn,
                args=(conn, addr),
                daemon=True
            )
            t.start()

    t = threading.Thread(target=accept_loop, daemon=True)
    t.start()
    return actual_port