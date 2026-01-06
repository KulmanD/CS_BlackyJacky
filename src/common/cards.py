import random

# suits encoding: 0..3 (h d c s) - pick one mapping and keep it consistent
suits = [0, 1, 2, 3]

def rank_value(rank: int) -> int:
    # 1..13 where 1 means ace, 11..13 mean j q k
    if rank == 1:
        return 11
    if rank >= 11:
        return 10
    return rank

def encode_card(rank: int, suit: int) -> bytes:
    # pdf says: first 2 bytes rank 01..13, second byte suit 0..3
    # easiest: rank as unsigned short (2 bytes), suit as unsigned byte (1 byte)
    rank = max(1, min(13, int(rank)))
    suit = max(0, min(3, int(suit)))
    return rank.to_bytes(2, "big") + bytes([suit])

def decode_card(card3: bytes):
    rank = int.from_bytes(card3[:2], "big")
    suit = card3[2]
    return rank, suit

class deck:
    def __init__(self):
        self.cards = []
        for suit in suits:
            for rank in range(1, 14):
                self.cards.append((rank, suit))
        random.shuffle(self.cards)

    def draw(self):
        if not self.cards:
            # reshuffle if empty (simple)
            self.__init__()
        return self.cards.pop()

class hand:
    def __init__(self):
        self.items = []

    def add(self, card):
        self.items.append(card)

    def total(self) -> int:
        s = 0
        for r, _ in self.items:
            s += rank_value(r)
        return s

    def is_bust(self) -> bool:
        return self.total() > 21