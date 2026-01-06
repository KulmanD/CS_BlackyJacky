import socket
import time
from common.constants import udp_offer_port
from common.protocol import pack_offer

def run_udp_broadcaster(tcp_port: int, server_name: str, stop_flag):
    # broadcasts offer every 1 second
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    msg = pack_offer(tcp_port, server_name)

    while not stop_flag["stop"]:
        try:
            s.sendto(msg, ("<broadcast>", udp_offer_port))
        except Exception:
            pass
        time.sleep(1.0)