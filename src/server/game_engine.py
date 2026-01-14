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
    # Initial temporary ID
    client_id = f"{addr[0]}:{addr[1]}"
    print(f"\nNew connection from {client_id}. Waiting for protocol handshake...")

    try:
        conn.settimeout(600)  # 10 minutes timeout

        req = recv_exact(conn, request_len)
        parsed = unpack_request(req)
        if parsed is None:
            print(f"[{client_id}] Sent invalid REQUEST packet. closing.")
            conn.close()
            return

        rounds, client_name = parsed
        # Update ID to include the Team Name
        client_id = f"{client_name}"
        print(f"\n[{client_id}] Handshake complete. Wants to play {rounds} rounds.")

        for i in range(rounds):
            print(f"\n=== Round {i + 1}/{rounds} for {client_id} ===")
            play_one_round(conn, client_id)
            print(f"=== Round {i + 1} Finished for {client_id} ===\n")

    except ConnectionError:
        print(f"[{client_id}] Disconnected abruptly.")

    except Exception as e:
        print(f"[{client_id}] Server Error: {e}")
        traceback.print_exc()
    finally:
        try:
            conn.close()
            print(f"[{client_id}] Connection closed.")
        except Exception:
            pass


def play_one_round(conn, client_id):
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
            c = d.draw()
            player.add(c)
            print(f"[{client_id}] ACTION: Hit -> Drew {rank_value(c[0])}. Total: {player.total()}")

            if player.is_bust():
                print(f"[{client_id}] RESULT: PLAYER Busted! (Total {player.total()} > 21). Sending LOSS.")
                conn.sendall(pack_server_payload(res_loss, encode_card(c[0], c[1])))
                return  # End round
            else:
                conn.sendall(pack_server_payload(res_not_over, encode_card(c[0], c[1])))
            continue

        elif decision5 == b"Stand":
            print(f"[{client_id}] ACTION: Stand. Final Player Total: {player.total()}")
            break
        else:
            print(f"[{client_id}] Received unknown command. Stopping round.")
            break

    # Dealer Turn
    # always reveal the hidden card first (round is still not over)
    hidden = dealer.items[1]
    if dealer.is_bust():
        conn.sendall(pack_server_payload(res_loss, encode_card(hidden[0], hidden[1])))
        return
    if dealer.total() < 17:
        conn.sendall(pack_server_payload(res_not_over, encode_card(hidden[0], hidden[1])))

    # dealer draws until reaching 17 or more
    last = encode_card(hidden[0], hidden[1])
    while dealer.total() < 17:
        print(f"[Dealer] has {dealer.total()}, drawing...")
        c = d.draw()
        dealer.add(c)
        print(f"[Dealer] Drew {rank_value(c[0])}. New Total: {dealer.total()}")

        # if dealer busts on this draw, send the busting card with the final WIN result
        if dealer.is_bust():
            conn.sendall(pack_server_payload(res_win, encode_card(c[0], c[1])))
            print(f"[{client_id}] RESULT: PLAYER WIN -- > Dealer Busted with value: {dealer.total()}")
            return

        # otherwise, keep sending cards as not-over
        if dealer.total() < 17:
            conn.sendall(pack_server_payload(res_not_over, encode_card(c[0], c[1])))
            print(f"Dealer Drew {rank_value(c[0])}. New Total: {dealer.total()}")
        else :
            last = encode_card(c[0], c[1])
    print(f"[Dealer] current score: {dealer.total()}")
    # Final Result
    p = player.total()
    dlr = dealer.total()

    if dealer.is_bust():
        final = res_win
        print(f"[{client_id}] RESULT: PLAYER WIN (Dealer Busted)")
    elif p > dlr:
        final = res_win
        print(f"[{client_id}] RESULT: PLAYER WIN {p} > {dlr}")
    elif p < dlr:
        final = res_loss
        print(f"[{client_id}] RESULT: CLIENT LOSS {p} < {dlr}")
    else:
        final = res_tie
        print(f"Tie ({p} vs {dlr}).")

    conn.sendall(pack_server_payload(final, last))