# Blackjack Network Game (CS_BlackyJacky)

This project implements a simplified blackjack game using a client–server model over a network.  
It follows the specification provided in the *Intro to Computer Networks 2025 Hackathon* assignment.

This README is written **for graders** who already know the assignment.  
It focuses on **how we implemented the system**, the **absolute execution flow**, and **non-standard / extra design choices**.

---

## Project Structure

```
common/
  constants.py      # protocol constants (cookie, ports, sizes)
  protocol.py       # binary pack/unpack helpers
  cards.py          # card + deck logic
  net_utils.py      # recv_exact() and helpers

server/
  main_server.py    # server entry point
  tcp_server.py     # tcp accept loop + threading
  udp_broadcast.py  # udp offer broadcaster
  game_engine.py    # blackjack logic

client/
  main_client.py    # client entry point
  udp_listener.py   # udp discovery
  tcp_client.py     # game session logic
  ui.py             # interactive output helpers

test_edge_cases.py  # stress & robustness tests
```

---

## Absolute Server Flow

1. `main_server.py` starts.
2. Server binds a TCP socket to `0.0.0.0` with port `0` (OS assigns a free port).
3. `run_tcp_server()` is called:
   - starts an accept loop
   - each incoming client is handled in its own thread
4. A UDP broadcaster thread is started:
   - sends offer packets once per second
   - includes magic cookie, message type, TCP port, and server name
5. The main server thread blocks on `input()`:
   - pressing **Enter** sets a shared `stop_flag`
   - UDP broadcast thread exits cleanly
   - server shuts down gracefully

---

## Client Flow

1. `main_client.py` starts.
2. User enters:
   - team name
   - number of rounds
3. Client listens on UDP port `13122`.
4. Upon receiving a valid offer:
   - extracts server IP and TCP port
   - connects via TCP
5. Client plays the requested number of rounds.
6. After session ends:
   - client returns to listening state
   - no restart required

---

## Game Flow (Single Round)

1. Server deals:
   - 2 cards to player
   - 2 cards to dealer (1 hidden)
2. Server sends:
   - player card
   - player card
   - dealer up-card
3. Client repeatedly sends:
   - `Hittt` or `Stand`
4. Server behavior:
   - on hit → send card + `RES_NOT_OVER`
   - on bust → send **final loss packet immediately**
5. Dealer draws until total ≥ 17.
6. Server sends final result:
   - win / loss / tie
   - dummy card if needed

---

## Non-Standard / Extra Design Choices

### Graceful Shutdown
- Server waits for **Enter** instead of forced termination.
- UDP broadcaster terminates via shared `stop_flag`.

### One-Packet Bust Notification
- When player busts, server sends:
  - bust card
  - loss result
- Done in a **single payload** to avoid deadlock.

### Interactive Client Output
Client UI prints:
- card symbols (♠ ♥ ♦ ♣)
- running hand totals
- round banners
- session summary with win-rate

All UI improvements are **client-side only** and do not alter the protocol.

### Robust Error Handling
- Malformed packets raise controlled `ConnectionError`.
- Only the offending client thread exits.
- Server continues serving other clients.

### Stress & Robustness Testing
`test_edge_cases.py` intentionally tests:
- player busts
- dealer busts and ties
- malformed cookies
- truncated payloads
- zero and high round counts
- random strategies
- concurrent clients

Server survives all tests without process termination.

---

## Why This Design

- Strict separation of protocol logic (`common/`)
- Thread-per-client model for clarity
- Defensive TCP reads (`recv_exact`)
- Deterministic and readable server logs
- Grader-friendly structure and flow

---

## Running the Project

Server:
```
python3 -m server.main_server
```

Client:
```
python3 -m client.main_client
```

Optional debugging:
```
DEBUG_OFFERS=1 python3 -m client.main_client
```

---

## Note to Graders

This README intentionally avoids restating the assignment text.  
All packet formats, sizes, and semantics strictly follow the official specification.

Extra UI, graceful shutdown handling, and stress tests were added for clarity,
robustness, and ease of demonstration.
