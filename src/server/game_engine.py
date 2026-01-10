from common.net_utils import recv_exact
from common.constants import request_len, client_payload_len
from common.protocol import unpack_request, pack_server_payload, unpack_client_payload
from common.cards import deck, hand, encode_card, rank_value
import traceback  # for error printing

# result codes
res_not_over = 0x0
res_tie = 0x1
res_loss = 0x2
res_win = 0x3


def handle_client(conn, addr):
    print(f"\n\n[DEBUG] New client connected: {addr}")
    try:
        conn.settimeout(600)  # timeout

        req = recv_exact(conn, request_len)
        parsed = unpack_request(req)
        if parsed is None:
            print("[DEBUG] Invalid REQUEST packet")
            conn.close()
            return

        rounds, client_name = parsed
        print(f"[DEBUG] Client '{client_name}' wants {rounds} rounds.")

        for i in range(rounds):
            print(f"\n[DEBUG] --- Starting Round {i + 1} ---")
            play_one_round(conn)
            print(f"[DEBUG] --- Finished Round {i + 1} ---\n")

    except ConnectionError:
        print(f"[DEBUG] Client {addr} disconnected abruptly (Bye!).")

    except Exception as e:
        print(f"!!! CRITICAL SERVER CRASH !!!")
        print(f"Error: {e}")
        traceback.print_exc()  # prints the exact line number
    finally:
        try:
            conn.close()
            print("[DEBUG] Connection closed.\n\n")
        except Exception:
            pass

def play_one_round(conn):
    d = deck()
    player = hand()
    dealer = hand()

    # deal initial cards
    player.add(d.draw())
    player.add(d.draw())
    dealer.add(d.draw())  # up card
    dealer.add(d.draw())  # hidden card

    # send player's cards
    print("[DEBUG] Sending player cards...")
    for card in player.items:
        conn.sendall(pack_server_payload(res_not_over, encode_card(card[0], card[1])))

    # send dealer's UP card only
    print("[DEBUG] Sending dealer up card...")
    up = dealer.items[0]
    conn.sendall(pack_server_payload(res_not_over, encode_card(up[0], up[1])))

    # player turn loop
    while True:
        # wait for decision
        pkt = recv_exact(conn, client_payload_len)
        decision5 = unpack_client_payload(pkt)

        if decision5 is None:
            raise ConnectionError("Client sent bad payload")

        if decision5 == b"Hittt":
            print("[DEBUG] Player hit.")
            c = d.draw()
            player.add(c)

            if player.is_bust():
                print(f"[DEBUG] Player drew {rank_value(c[0])} and busted with {player.total()}.")
                # send the card and the loss result in one packet
                conn.sendall(pack_server_payload(res_loss, encode_card(c[0], c[1])))
                return  # end round immediately
            else:
                # send the card and continue
                conn.sendall(pack_server_payload(res_not_over, encode_card(c[0], c[1])))
            continue

        elif decision5 == b"Stand":
            print("[DEBUG] Player stood.")
            break
        else:
            break

    # dealer turn (only reachable if player didn't bust)
    print("[DEBUG] Revealing dealer hidden card...")
    hidden = dealer.items[1]
    conn.sendall(pack_server_payload(res_not_over, encode_card(hidden[0], hidden[1])))

    while dealer.total() < 17:
        print(f"[DEBUG] Dealer has {dealer.total()}, drawing...")
        c = d.draw()
        dealer.add(c)
        conn.sendall(pack_server_payload(res_not_over, encode_card(c[0], c[1])))

    # final compare
    print("[DEBUG] Calculating winner...")
    p = player.total()
    dlr = dealer.total()

    if dealer.is_bust():
        final = res_win
    elif p > dlr:
        final = res_win
    elif p < dlr:
        final = res_loss
    else:
        final = res_tie

    print(f"[DEBUG] Result: {final}")
    conn.sendall(pack_server_payload(final, b"\x00\x00\x00"))