import struct
from .constants import (
    magic_cookie, msg_type_offer, msg_type_request, msg_type_payload,
    name_len, decision_len, card_len)

from .net_utils import pad_name, read_name

########## UDP
def pack_offer(tcp_port: int, server_name: str) -> bytes:
    # cookie (4), type (1), port (2), name (32)
    return struct.pack("!IBH", magic_cookie, msg_type_offer, tcp_port) + pad_name(server_name, name_len)

def unpack_offer(data: bytes):
    # returns (tcp_port, server_name) or None if invalid
    if len(data) != 4 + 1 + 2 + name_len:
        return None
    cookie, mtype, tcp_port = struct.unpack("!IBH", data[:7])
    if cookie != magic_cookie or mtype != msg_type_offer:
        return None
    name = read_name(data[7:7 + name_len])
    return tcp_port, name
##########
########## TCP hand shake
def pack_request(rounds: int, client_name: str) -> bytes:
    # cookie (4), type (1), rounds (1), name (32)
    rounds = max(0, min(255, int(rounds)))
    return struct.pack("!IBB", magic_cookie, msg_type_request, rounds) + pad_name(client_name, name_len)

def unpack_request(data: bytes):
    if len(data) != 4 + 1 + 1 + name_len:
        return None
    cookie, mtype, rounds = struct.unpack("!IBB", data[:6])
    if cookie != magic_cookie or mtype != msg_type_request:
        return None
    name = read_name(data[6:6 + name_len])
    return rounds, name
##########
########## TCP decision (payload)
def pack_client_payload(decision5: bytes) -> bytes:
    # client -> server payload:
    # cookie (4), type (1), decision(5)
    if not isinstance(decision5, (bytes, bytearray)) or len(decision5) != decision_len:
        raise ValueError("decision must be 5 bytes")
    return struct.pack("!IB", magic_cookie, msg_type_payload) + decision5


def unpack_client_payload(data: bytes):
    # returns decision (5 bytes) or None if invalid
    expected_len = 4 + 1 + decision_len
    if len(data) != expected_len:
        return None
    cookie, mtype = struct.unpack("!IB", data[:5])
    if cookie != magic_cookie or mtype != msg_type_payload:
        return None
    decision = data[5:5 + decision_len]
    if len(decision) != decision_len:
        return None
    return decision
###########
########### TCP result + card
def pack_server_payload(result: int, card3: bytes) -> bytes:
    # server -> client payload:
    # cookie (4), type (1), result(1), card(3)
    if not isinstance(card3, (bytes, bytearray)) or len(card3) != card_len:
        raise ValueError("card must be 3 bytes")
    if not isinstance(result, int) or not (0 <= result <= 255):
        raise ValueError("result must be an int in range 0..255")
    return (
        struct.pack("!IB", magic_cookie, msg_type_payload)
        + struct.pack("!B", result & 0xff)
        + card3
    )


def unpack_server_payload(data: bytes):
    # returns (result, card3) or None if invalid
    expected_len = 4 + 1 + 1 + card_len
    if len(data) != expected_len:
        return None
    cookie, mtype = struct.unpack("!IB", data[:5])
    if cookie != magic_cookie or mtype != msg_type_payload:
        return None
    result = data[5]
    card = data[6:6 + card_len]
    if len(card) != card_len:
        return None
    return result, card
############