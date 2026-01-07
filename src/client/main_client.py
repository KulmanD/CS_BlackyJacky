from client.udp_listener import listen_for_offer
from client.tcp_client import play_session
from client.ui import ask_rounds, ask_name


def main():
    print("--- Client Started ---")

    # get user info
    team_name = ask_name()
    rounds = ask_rounds()

    while True:
        print(f"Listening for offers on UDP port...")

        # wait for a server offer
        offer = listen_for_offer()

        if offer is None:
            # no offer received in 1 second, loop back and try again
            continue

        server_ip, server_port, server_name = offer
        print(f"Received offer from '{server_name}' at {server_ip}")

        # connect and play
        play_session(server_ip, server_port, rounds, team_name)

        # After game finishes, loop back to listening
        print("Game over. Searching for new server...\n")


if __name__ == "__main__":
    main()