from common.net_utils import recv_exact
from common.constants import payload_len, request_len
from common.protocol import unpack_request, pack_payload, unpack_payload
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

    # send initial state to client using payload packets (simple approach: send cards as separate payloads)
    # decision field ignored by client on server->client packets, so just send b"-----"
    dummy_dec = b"-----"

    # send player's two cards
    for card in player.items:
        conn.sendall(pack_payload(dummy_dec, res_not_over, encode_card(card[0], card[1])))

    # send dealer upcard only
    up = dealer.items[0]
    conn.sendall(pack_payload(dummy_dec, res_not_over, encode_card(up[0], up[1])))

    # player turn
    while True:
        if player.is_bust():
            conn.sendall(pack_payload(dummy_dec, res_loss, b"\x00\x00\x00"))
            return

        pkt = recv_exact(conn, payload_len)
        payload = unpack_payload(pkt)
        if payload is None:
            raise ConnectionError("bad payload")

        decision5, _, _ = payload
        if decision5 == b"Hittt":
            c = d.draw()
            player.add(c)
            conn.sendall(pack_payload(dummy_dec, res_not_over, encode_card(c[0], c[1])))
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
        conn.sendall(pack_payload(dummy_dec, res_not_over, encode_card(c[0], c[1])))

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

    conn.sendall(pack_payload(dummy_dec, final, b"\x00\x00\x00"))