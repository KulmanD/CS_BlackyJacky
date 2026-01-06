import socket
from common.net_utils import recv_exact
from common.constants import request_len, payload_len
from common.protocol import pack_request, pack_payload, unpack_payload
from common.cards import decode_card, rank_value

# result codes
res_not_over = 0x0
res_tie = 0x1
res_loss = 0x2
res_win = 0x3

def play_session(server_ip: str, tcp_port: int, rounds: int, name: str):
    wins = 0
    losses = 0
    ties = 0

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(15)
    s.connect((server_ip, tcp_port))

    s.sendall(pack_request(rounds, name))

    for i in range(rounds):
        result = play_one_round(s)
        if result == res_win:
            wins += 1
        elif result == res_loss:
            losses += 1
        elif result == res_tie:
            ties += 1

    s.close()

    total = wins + losses + ties
    win_rate = (wins / total) if total > 0 else 0.0
    print(f"finished playing {total} rounds, win rate: {win_rate:.2f}")
    return wins, losses, ties

def play_one_round(sock: socket.socket):
    # simple client: it prints cards as they arrive.
    # it does not try to perfectly model hidden dealer card (you can improve later).

    # get initial 3 cards: player, player, dealer upcard
    for _ in range(3):
        decision, result, card3 = unpack_payload(recv_exact(sock, payload_len))
        r, suit = decode_card(card3)
        print(f"card: rank={r} suit={suit}")

    # decision loop
    while True:
        # ask user
        from client.ui import ask_hit_or_stand
        d = ask_hit_or_stand()

        if d == "hit":
            sock.sendall(pack_payload(b"Hittt", 0, b"\x00\x00\x00"))
        else:
            sock.sendall(pack_payload(b"Stand", 0, b"\x00\x00\x00"))

        # read server updates until either (a) new card, or (b) final result
        decision, result, card3 = unpack_payload(recv_exact(sock, payload_len))

        if result in (res_win, res_loss, res_tie):
            return result

        # not over: server sent a card (player card or dealer card)
        r, suit = decode_card(card3)
        print(f"card: rank={r} suit={suit}")

        # keep looping; server will later send final result after dealer turn