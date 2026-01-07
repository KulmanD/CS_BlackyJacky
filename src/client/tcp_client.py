import socket
from common.constants import request_len, server_payload_len, client_payload_len
from common.protocol import pack_request, pack_client_payload, unpack_server_payload
from common.net_utils import recv_exact
from common.cards import decode_card
from client.ui import ask_hit_or_stand

# Result codes from assignment
RES_NOT_OVER = 0x0
RES_TIE = 0x1
RES_LOSS = 0x2
RES_WIN = 0x3


def play_session(ip, port, rounds, name):
    print(f"\n--- Connecting to {ip}:{port} ---")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(600)  # safety timeout
        sock.connect((ip, port))

        # sends request packet (name + rounds)
        req_packet = pack_request(rounds, name)
        sock.sendall(req_packet)

        wins = 0

        for i in range(rounds):
            print(f"\n=== Round {i + 1} of {rounds} ===")
            result = play_one_round(sock)

            if result == RES_WIN:
                print("Result: YOU WIN!")
                wins += 1
            elif result == RES_LOSS:
                print("Result: DEALER WINS.")
            else:
                print("Result: TIE.")

        print(f"\n--- Session Ended. You won {wins}/{rounds} rounds. ---")
        sock.close()

    except Exception as e:
        print(f"Connection Error: {e}")


def play_one_round(sock):
    """handles the flow of a single round."""

    # --- Phase 1: Initial Deal (3 Cards) ---
    # Server sends: [Player Card 1] -> [Player Card 2] -> [Dealer Up Card]
    print("Waiting for cards...")
    try:
        for i in range(3):
            data = recv_exact(sock, server_payload_len)
            res, card_bytes = unpack_server_payload(data)

            rank, suit = decode_card(card_bytes)
            who = "Dealer" if i == 2 else "Player"
            print(f"[{who}] Dealt: Rank {rank}, Suit {suit}")
    except Exception as e:
        print(f"Error getting initial cards: {e}")
        return RES_LOSS

    # --- Phase 2: Player Decisions ---
    while True:
        move = ask_hit_or_stand()

        if move == "hit":
            # send 'Hittt' (5 bytes)
            sock.sendall(pack_client_payload(b"Hittt"))

            # wait for card or bust
            data = recv_exact(sock, server_payload_len)
            res, card_bytes = unpack_server_payload(data)

            # if server says game over (Bust), stop immediately
            if res != RES_NOT_OVER:
                return res

            # otherwise print new card
            rank, suit = decode_card(card_bytes)
            print(f"[Player] Hit: Rank {rank}, Suit {suit}")

        else:
            # Send 'Stand' (5 bytes)
            sock.sendall(pack_client_payload(b"Stand"))
            print("Standing. Waiting for Dealer...")
            break

    # --- Phase 3: Dealer Turn & Results ---
    # we must listen repeatedly until the server sends a final result (WIN/LOSS/TIE)
    while True:
        data = recv_exact(sock, server_payload_len)
        res, card_bytes = unpack_server_payload(data)

        # If there is a valid card in this packet, show it (Dealer drawing)
        # Note: The final result packet usually contains a dummy card (0,0)
        if card_bytes != b'\x00\x00\x00':
            rank, suit = decode_card(card_bytes)
            # Only print if it looks like a real card
            if rank != 0:
                print(f"[Dealer] Drew: Rank {rank}, Suit {suit}")

        # If result is not 0, the round is over
        if res != RES_NOT_OVER:
            return res