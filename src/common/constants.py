# magic cookie and message types (from the pdf)
magic_cookie = 0xabcddcba

msg_type_offer = 0x2
msg_type_request = 0x3
msg_type_payload = 0x4

# udp port used for offers
udp_offer_port = 13122

# fixed field sizes (from the pdf)
name_len = 32
decision_len = 5
card_len = 3

# offer packet:
# magic (4) + type (1) + udp_port (2) + server_name (32)
offer_len = 4 + 1 + 2 + name_len

# request packet:
# magic (4) + type (1) + tcp_port (1) + client_name (32)
request_len = 4 + 1 + 1 + name_len

# payload packets (note: client and server have different structure)

# client -> server payload:
# magic (4) + type (1) + decision (5) = 10 bytes
client_payload_len = 4 + 1 + decision_len

# server -> client payload:
# magic (4) + type (1) + result (1) + card (3) = 9 bytes
server_payload_len = 4 + 1 + 1 + card_len
