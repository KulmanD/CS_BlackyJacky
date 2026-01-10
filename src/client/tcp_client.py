import socket
from common.constants import request_len, server_payload_len, client_payload_len
from common.protocol import pack_request, pack_client_payload, unpack_server_payload
from common.net_utils import recv_exact
from common.cards import decode_card, rank_value , suit_name
from client.ui import ask_hit_or_stand

# Result codes from assignment
RES_NOT_OVER = 0x0
RES_TIE = 0x1
RES_LOSS = 0x2
RES_WIN = 0x3


# --- fun printing helpers (client-side only) ---

def _card_pretty(rank, suit):
    # rank is 1..13 (ace..king), suit is 0..3
    faces = {1: "A", 11: "J", 12: "Q", 13: "K"}
    r = faces.get(rank, str(rank))

    # use unicode suit symbols if your terminal supports it
    suit_symbols = {
        0: "♥",  # hearts
        1: "♦",  # diamonds
        2: "♣",  # clubs
        3: "♠",  # spades
    }
    s = suit_symbols.get(suit, "?")

    return f"{r}{s}"


def _hand_total(cards):
    # assignment rule: ace always counts as 11
    return sum(rank_value(r) for (r, _s) in cards)


def _banner(text):
    line = "=" * (len(text) + 8)
    print(f"\n{line}\n=== {text} ===\n{line}")


def _say(text):
    # small consistent prefix
    print(f"🃏 {text}")


def play_session(ip, port, rounds, name):
    _banner(f"connecting to dealer @ {ip}:{port}")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(600)  # safety timeout
        sock.connect((ip, port))

        # sends request packet (name + rounds)
        req_packet = pack_request(rounds, name)
        sock.sendall(req_packet)

        wins = 0

        for i in range(rounds):
            _banner(f"round {i + 1} / {rounds}")
            result = play_one_round(sock)

            if result == RES_WIN:
                _say(" you win this round!")
                wins += 1
            elif result == RES_LOSS:
                _say(" dealer wins this round.")
            else:
                _say(" tie round.")

        win_rate = (wins / rounds) if rounds else 0
        _banner("session summary")
        _say(f"final score: {wins}/{rounds} wins")
        _say(f"win rate: {win_rate:.1%}")
        sock.close()

    except Exception as e:
        print(f"Connection Error: {e}")


def play_one_round(sock):
    """handles the flow of a single round."""

    # --- Phase 1: Initial Deal (3 Cards) ---
    # Server sends: [Player Card 1] -> [Player Card 2] -> [Dealer Up Card]
    _say("shuffling... dealing initial cards")
    player_cards = []
    dealer_cards = []
    try:
        for i in range(3):
            data = recv_exact(sock, server_payload_len)
            res, card_bytes = unpack_server_payload(data)

            rank, suit = decode_card(card_bytes)

            if i == 2:
                dealer_cards.append((rank, suit))
                _say(f"dealer shows: {_card_pretty(rank, suit)}")
            else:
                player_cards.append((rank, suit))
                _say(f"you get: {_card_pretty(rank, suit)}")

            # after the second player card, show your starting hand + total
            if i == 1:
                pretty = " ".join(_card_pretty(r, s) for (r, s) in player_cards)
                _say(f"your hand: {pretty}  (total: {_hand_total(player_cards)})")
    except Exception as e:
        print(f"Error getting initial cards: {e}")
        return RES_LOSS

    _say("your move: hit or stand")

    # --- Phase 2: Player Decisions ---
    while True:
        move = ask_hit_or_stand()

        if move == "hit":
            sock.sendall(pack_client_payload(b"Hittt"))

            data = recv_exact(sock, server_payload_len)
            res, card_bytes = unpack_server_payload(data)

            # Always print the card if it exists, even if we busted
            if card_bytes != b'\x00\x00\x00':
                rank, suit = decode_card(card_bytes)
                player_cards.append((rank, suit))
                pretty = " ".join(_card_pretty(r, s) for (r, s) in player_cards)
                _say(f"hit! you draw: {_card_pretty(rank, suit)}")
                _say(f"your hand: {pretty}  (total: {_hand_total(player_cards)})")

            if res == RES_LOSS:
                _say(" bust! you went over 21")

            if res != RES_NOT_OVER:
                return res  # Game over (Bust)

        else:
            # Send 'Stand' (5 bytes)
            sock.sendall(pack_client_payload(b"Stand"))
            pretty = " ".join(_card_pretty(r, s) for (r, s) in player_cards)
            _say(f"stand. you lock: {pretty}  (total: {_hand_total(player_cards)})")
            _say("dealer's turn...")
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
                dealer_cards.append((rank, suit))
                pretty = " ".join(_card_pretty(r, s) for (r, s) in dealer_cards)
                _say(f"dealer draws: {_card_pretty(rank, suit)}")
                _say(f"dealer hand: {pretty}  (total: {_hand_total(dealer_cards)})")

        # If result is not 0, the round is over
        if res != RES_NOT_OVER:
            _banner("round summary")
            p_pretty = " ".join(_card_pretty(r, s) for (r, s) in player_cards)
            d_pretty = " ".join(_card_pretty(r, s) for (r, s) in dealer_cards)
            _say(f"you:    {p_pretty}  (total: {_hand_total(player_cards)})")
            _say(f"dealer: {d_pretty}  (total: {_hand_total(dealer_cards)})")
            return res