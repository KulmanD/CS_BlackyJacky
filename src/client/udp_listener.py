import socket
from common.constants import udp_offer_port
from common.protocol import unpack_offer


def listen_for_offer(timeout_sec: float = 3.0):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", udp_offer_port))
        s.settimeout(timeout_sec)

        # wait until timeout for a valid offer packet
        while True:
            try:
                data, addr = s.recvfrom(2048)
            except socket.timeout:
                return None
            except Exception:
                return None

            parsed = unpack_offer(data)
            if parsed is None:
                # junk packet, keep listening until timeout
                continue

            tcp_port, server_name = parsed
            return addr[0], tcp_port, server_name
    finally:
        s.close()