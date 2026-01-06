import struct
from .constants import (
    magic_cookie, msg_type_offer, msg_type_request, msg_type_payload,
    name_len, decision_len
)
from .net_utils import pad_name, read_name

def pack_offer(tcp_port: int, server_name: str) -> bytes:
    # cookie (4), type (1), port (2), name (32)
    return struct.pack("!IBH", magic_cookie, msg_type_offer, tcp_port) + pad_name(server_name, name_len)

def unpack_offer(data: bytes):
    # returns (tcp_port, server_name) or None if invalid
    if len(data) < 4 + 1 + 2 + name_len:
        return None
    cookie, mtype, tcp_port = struct.unpack("!IBH", data[:7])
    if cookie != magic_cookie or mtype != msg_type_offer:
        return None
    name = read_name(data[7:7 + name_len])
    return tcp_port, name

def pack_request(rounds: int, client_name: str) -> bytes:
    # cookie (4), type (1), rounds (1), name (32)
    rounds = max(0, min(255, int(rounds)))
    return struct.pack("!IBB", magic_cookie, msg_type_request, rounds) + pad_name(client_name, name_len)

def unpack_request(data: bytes):
    if len(data) < 4 + 1 + 1 + name_len:
        return None
    cookie, mtype, rounds = struct.unpack("!IBB", data[:6])
    if cookie != magic_cookie or mtype != msg_type_request:
        return None
    name = read_name(data[6:6 + name_len])
    return rounds, name

def pack_payload(decision5: bytes, result: int, card3: bytes) -> bytes:
    # cookie (4), type (1), decision(5), result(1), card(3)
    if len(decision5) != decision_len:
        raise ValueError("decision must be 5 bytes")
    if len(card3) != 3:
        raise ValueError("card must be 3 bytes")
    return struct.pack("!IB", magic_cookie, msg_type_payload) + decision5 + struct.pack("!B", result & 0xff) + card3

def unpack_payload(data: bytes):
    if len(data) < 4 + 1 + decision_len + 1 + 3:
        return None
    cookie, mtype = struct.unpack("!IB", data[:5])
    if cookie != magic_cookie or mtype != msg_type_payload:
        return None
    decision = data[5:5 + decision_len]
    result = data[10]
    card = data[11:14]
    return decision, result, card