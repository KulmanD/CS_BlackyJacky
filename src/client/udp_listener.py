import socket
from common.constants import udp_offer_port, offer_len
#expected offer_len = magic(4) + type(1) + tcp_port(2) + server_name(32)
from common.protocol import unpack_offer

"""
Listens for UDP offers and lets the user choose which server to connect to.

Behavior:
- keeps listening and printing discovered servers (deduped by ip+port)
- press ENTER to keep listening for more offers
- type a number to select a server from the list
- type 'q' to quit selection (returns None)

Returns:
- (server_ip, tcp_port, server_name) when user selects one
- None if user quits or no valid servers were found
"""

def listen_for_offer():
    # create UDP socket (IPv4 + UDP)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # map: (ip, tcp_port) -> server_name
    seen = {}

    try:
        # allow multiple clients to listen on the same machine
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

        # listen on all interfaces on the offer port
        s.bind(("", udp_offer_port))

        print("listening for server offers... (press enter to refresh list, number to pick, q to quit)")

        while True:
            # short timeout so we can keep printing / accepting user choices
            s.settimeout(1.0)

            try:
                data, addr = s.recvfrom(offer_len)
            except socket.timeout:
                data = None
            except Exception as e:
                print(f"udp error: {e}")
                data = None

            # if we received something, try to parse it as an offer
            if data is not None:
                parsed = unpack_offer(data)
                if parsed is not None:
                    tcp_port, server_name = parsed
                    server_ip = addr[0]

                    key = (server_ip, tcp_port)
                    # store newest name we saw for this ip+port
                    if key not in seen:
                        print(f"found server: name='{server_name}' ip={server_ip} tcp_port={tcp_port}")
                    seen[key] = server_name

            # show menu prompt every loop, so user can pick at any time
            if seen:
                print("\nservers discovered:")
                items = list(seen.items())
                for idx, ((ip, port), name) in enumerate(items, start=1):
                    print(f"  {idx}) {name} @ {ip}:{port}")
            else:
                print("\n(no servers discovered yet)")

            choice = input("choose server (enter=keep listening, number=select, q=quit): ").strip().lower()
            if choice == "":
                # keep listening
                continue
            if choice == "q":
                return None

            # try parse number
            try:
                n = int(choice)
            except ValueError:
                print("invalid input. type a number, enter, or q.")
                continue

            items = list(seen.items())
            if 1 <= n <= len(items):
                (ip, port), name = items[n - 1]
                return ip, port, name
            else:
                print("number out of range.")

    finally:
        s.close()