from common.net_utils import recv_exact
from common.constants import request_len, client_payload_len
from common.protocol import unpack_request, pack_server_payload, unpack_client_payload
from common.cards import deck, hand, encode_card, rank_value
import traceback

# result codes
res_not_over = 0x0
res_tie = 0x1
res_loss = 0x2
res_win = 0x3


def handle_client(conn, addr):
    # Print IP only once at connection
    print(f"\nNew connection from {addr[0]}:{addr[1]}")

    try:
        conn.settimeout(600)  # 10 minutes timeout

        req = recv_exact(conn, request_len)
        parsed = unpack_request(req)
        if parsed is None:
            print("Invalid REQUEST packet. Closing.")
            conn.close()
            return

        rounds, client_name = parsed
        print(f"Client '{client_name}' identified. Playing {rounds} rounds.\n")

        for i in range(rounds):
            play_one_round(conn, client_name)

    except ConnectionError:
        print(f"Client {client_name} , IP {addr[0]} Port: {addr[1]} disconnected.")

    except Exception as e:
        print(f"Server error: {e}")
        traceback.print_exc()
    finally:
        try:
            conn.close()
        except Exception:
            pass


def play_one_round(conn, client_name):
    d = deck()
    player = hand()
    dealer = hand()

    # Deal initial cards
    player.add(d.draw())
    player.add(d.draw())
    dealer.add(d.draw())  # Up card
    dealer.add(d.draw())  # Hidden card

    # Send initial cards
    for card in player.items:
        conn.sendall(pack_server_payload(res_not_over, encode_card(card[0], card[1])))

    up = dealer.items[0]
    conn.sendall(pack_server_payload(res_not_over, encode_card(up[0], up[1])))

    # Player Turn Loop
    while True:
        pkt = recv_exact(conn, client_payload_len)
        decision5 = unpack_client_payload(pkt)

        if decision5 is None:
            raise ConnectionError("Client sent bad payload")

        if decision5 == b"Hittt":
            print(f"{client_name} hit.")
            c = d.draw()
            player.add(c)

            if player.is_bust():
                print(f"{client_name} busted with {player.total()}.")
                conn.sendall(pack_server_payload(res_loss, encode_card(c[0], c[1])))
                return  # End round
            else:
                conn.sendall(pack_server_payload(res_not_over, encode_card(c[0], c[1])))
            continue

        elif decision5 == b"Stand":
            print(f"{client_name} stands.")
            break
        else:
            break

    # Dealer Turn
    hidden = dealer.items[1]
    conn.sendall(pack_server_payload(res_not_over, encode_card(hidden[0], hidden[1])))

    while dealer.total() < 17:
        print(f"Dealer has {dealer.total()}, drawing...")
        c = d.draw()
        dealer.add(c)
        conn.sendall(pack_server_payload(res_not_over, encode_card(c[0], c[1])))

    # Final Result
    p = player.total()
    dlr = dealer.total()

    if dealer.is_bust():
        final = res_win
        print(f"Dealer busted. {client_name} wins.")
    elif p > dlr:
        final = res_win
        print(f"{client_name} wins ({p} vs {dlr}).")
    elif p < dlr:
        final = res_loss
        print(f"Dealer wins ({dlr} vs {p}).")
    else:
        final = res_tie
        print(f"Tie ({p} vs {dlr}).")

    conn.sendall(pack_server_payload(final, b"\x00\x00\x00"))