import socket
import time
from common.constants import udp_offer_port
from common.protocol import pack_offer


def run_udp_broadcaster(tcp_port: int, server_name: str, stop_flag):
    # broadcasts offer every 1 second
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        while not stop_flag.get("stop", False):
            try:
                msg = pack_offer(tcp_port, server_name)
                s.sendto(msg, ("<broadcast>", udp_offer_port))
            except Exception:
                # ignore transient network errors, keep broadcasting
                pass

            time.sleep(1.0)
    finally:
        s.close()