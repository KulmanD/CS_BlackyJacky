from client.udp_listener import listen_for_offer
from client.tcp_client import play_session
from client.ui import ask_rounds, ask_name


def main():
    print("--- Client Started ---")

    try:
        # get user info
        team_name = ask_name()
        rounds = ask_rounds()

        while True:
            print(f"Listening for offers on UDP port...")
            offer = listen_for_offer() # wait for a server offer

            if offer is None:
                continue # no offer received in 1 second, loop back and try again

            server_ip, server_port, server_name = offer
            print(f"Received offer from '{server_name}' at {server_ip}")

            #here we create the tcp socket
            #blocking call, meaning it doesn't return till session end or interrupt
            play_session(server_ip, server_port, rounds, team_name) # connect and play

            print("Game over. Searching for new server...\n") # after game finishes, loop back to listening

    except KeyboardInterrupt: # pressed control c
        print("\n[Client] User requested shutdown. Goodbye!")


if __name__ == "__main__":
    main()