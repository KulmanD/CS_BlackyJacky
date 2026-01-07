import threading
from src.server.udp_broadcast import run_udp_broadcaster
from src.server.tcp_server import run_tcp_server
from src.server.game_engine import handle_client


def main():
    bind_ip = "0.0.0.0"
    bind_port = 0  # let os choose
    server_name = "dealer"

    stop_flag = {"stop": False}

    tcp_port = run_tcp_server(bind_ip, bind_port, handle_client)

    t = threading.Thread(target=run_udp_broadcaster, args=(tcp_port, server_name, stop_flag), daemon=True)
    t.start()

    print(f"server up on tcp port {tcp_port}")
    try:
        while True:
            input()  # press enter to quit
    except KeyboardInterrupt:
        pass
    stop_flag["stop"] = True


if __name__ == "__main__":
    main()