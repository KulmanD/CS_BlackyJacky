import socket
from common.constants import udp_offer_port
from common.protocol import unpack_offer

def listen_for_offer(timeout_sec: float = 3.0):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", udp_offer_port))
    s.settimeout(timeout_sec)

    try:
        data, addr = s.recvfrom(2048)
        parsed = unpack_offer(data)
        if parsed is None:
            return None
        tcp_port, server_name = parsed
        return addr[0], tcp_port, server_name
    except Exception:
        return None
    finally:
        s.close()