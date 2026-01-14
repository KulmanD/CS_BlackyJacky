import socket
from common.constants import udp_offer_port, offer_len
#expected offer_len = magic(4) + type(1) + tcp_port(2) + server_name(32)
from common.protocol import unpack_offer

"""
Listens for a UDP broadcast on port 13122.
Returns: (server_ip, server_port, server_name) or None if timed out/invalid.
"""
def listen_for_offer():

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # allow multiple clients to listen on the same machine
    try:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        s.bind(("", udp_offer_port))

        s.settimeout(1.0) # don't block forever, check every second so we can stop the program if needed

        try:
            data, addr = s.recvfrom(offer_len) # we need at least offer_len bytes
        except socket.timeout:
            return None
        except Exception as e:
            print(f"UDP Error: {e}")
            return None

        parsed = unpack_offer(data) # use protocol file to unpack
        if parsed is None:
            return None

        tcp_port, server_name = parsed
        return addr[0], tcp_port, server_name

    finally:
        s.close()