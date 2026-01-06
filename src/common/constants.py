# all-lowercase everyday comments

# magic cookie and message types (from the pdf)
magic_cookie = 0xabcddcba

msg_type_offer = 0x2
msg_type_request = 0x3
msg_type_payload = 0x4

udp_offer_port = 13122

# fixed field sizes
name_len = 32
decision_len = 5
offer_len = 4 + 1 + 2 + name_len
request_len = 4 + 1 + 1 + name_len
payload_len = 4 + 1 + decision_len + 1 + 3