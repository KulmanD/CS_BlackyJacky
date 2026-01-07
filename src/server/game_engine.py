from common.net_utils import recv_exact
from common.constants import request_len, client_payload_len
from common.protocol import unpack_request, pack_server_payload, unpack_client_payload
from common.cards import deck, hand, encode_card

# result codes (from pdf)
res_not_over = 0x0
res_tie = 0x1
res_loss = 0x2
res_win = 0x3

def handle_client(conn, addr):
    try:
        conn.settimeout(15)

        req = recv_exact(conn, request_len)
        parsed = unpack_request(req)
        if parsed is None:
            conn.close()
            return

        rounds, client_name = parsed

        # play rounds
        for _ in range(rounds):
            play_one_round(conn)

    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

def play_one_round(conn):
    d = deck()
    player = hand()
    dealer = hand()

    # deal 2 each
    player.add(d.draw())
    player.add(d.draw())
    dealer.add(d.draw())
    dealer.add(d.draw())

    # send player's two cards
    for card in player.items:
        conn.sendall(pack_server_payload(res_not_over, encode_card(card[0], card[1])))

    # send dealer upcard only
    up = dealer.items[0]
    conn.sendall(pack_server_payload(res_not_over, encode_card(up[0], up[1])))

    # player turn
    while True:
        if player.is_bust():
            conn.sendall(pack_server_payload(res_loss, b"\x00\x00\x00"))
            return

        pkt = recv_exact(conn, client_payload_len)
        decision5 = unpack_client_payload(pkt)
        if decision5 is None:
            raise ConnectionError("bad payload")

        if decision5 == b"Hittt":
            c = d.draw()
            player.add(c)
            conn.sendall(pack_server_payload(res_not_over, encode_card(c[0], c[1])))
            continue
        elif decision5 == b"Stand":
            break
        else:
            # invalid decision, treat like stand (simple)
            break

    # dealer turn
    while dealer.total() < 17 and not dealer.is_bust():
        c = d.draw()
        dealer.add(c)
        conn.sendall(pack_server_payload(res_not_over, encode_card(c[0], c[1])))

    # final compare
    p = player.total()
    dlr = dealer.total()

    if player.is_bust():
        final = res_loss
    elif dealer.is_bust():
        final = res_win
    elif p > dlr:
        final = res_win
    elif p < dlr:
        final = res_loss
    else:
        final = res_tie

    conn.sendall(pack_server_payload(final, b"\x00\x00\x00"))