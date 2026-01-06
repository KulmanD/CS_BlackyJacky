from client.udp_listener import listen_for_offer
from client.tcp_client import play_session
from client.ui import ask_rounds, ask_name

def main():
    rounds = ask_rounds()
    name = ask_name()

    while True:
        offer = listen_for_offer()
        if offer is None:
            print("listening for offer...")
            continue

        ip, port, server_name = offer
        print(f"got offer from {server_name} at {ip}:{port}")

        try:
            play_session(ip, port, rounds, name)
        except Exception as e:
            print(f"session failed: {e}")

if __name__ == "__main__":
    main()