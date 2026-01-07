from udp_listener import listen_for_offer
from tcp_client import play_session
from ui import ask_rounds, ask_name
import time

def main():
    rounds = ask_rounds()
    name = ask_name()

    printed_listening = False

    while True:
        offer = listen_for_offer()
        if offer is None:
            if not printed_listening:
                print("listening for offer...")
                printed_listening = True
            time.sleep(0.1)
            continue

        printed_listening = False

        ip, port, server_name = offer
        print(f"got offer from {server_name} at {ip}:{port}")

        try:
            play_session(ip, port, rounds, name)
        except Exception as e:
            print(f"session failed: {e}")


if __name__ == "__main__":
    main()