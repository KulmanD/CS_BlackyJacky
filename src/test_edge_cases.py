import socket
import time

# Import server and protocol components. These imports assume the project
# structure follows the assignment's recommended layout where server and
# common are packages. If your server code lives under a different module
# path, adjust the imports accordingly.
try:
    from server.tcp_server import run_tcp_server
    from server.game_engine import handle_client, res_not_over, res_tie, res_loss, res_win
    from common.protocol import pack_request, pack_client_payload, unpack_server_payload
    from common.net_utils import recv_exact
    from common.constants import server_payload_len
except ImportError:
    raise ImportError(
        "Unable to import required modules. Make sure the project includes "
        "\"server\", \"common\", and related packages."
    )


class AlwaysHit:
    """Decision strategy that always hits."""
    def next_decision(self):
        return b"Hittt"


class AlwaysStand:
    """Decision strategy that stands on the first decision and then does nothing."""
    def __init__(self):
        self.sent = False

    def next_decision(self):
        if not self.sent:
            self.sent = True
            return b"Stand"
        return None


def run_session(tcp_port, strategy_factory, rounds=1):
    """Connects to the server and plays a given number of rounds using a strategy.

    Args:
        tcp_port (int): The TCP port of the running server.
        strategy_factory (callable): A function returning a new decision strategy for each round.
        rounds (int): Number of rounds to play in a single session.

    Returns:
        list[int]: A list of result codes for each round.
    """
    conn = socket.create_connection(("127.0.0.1", tcp_port))
    # Send the request: cookie + msg_type_request + number of rounds + padded team name
    conn.sendall(pack_request(rounds, "TestClient"))
    results = []

    for _ in range(rounds):
        strat = strategy_factory()
        awaiting_decision = False
        initial_msgs = 0
        while True:
            # Read the full server payload (always 9 bytes)
            data = recv_exact(conn, server_payload_len)
            res_code, card = unpack_server_payload(data)
            # If the result is not RES_NOT_OVER, the round is finished
            if res_code != res_not_over:
                results.append(res_code)
                break
            # After receiving two player cards and one dealer up card, start sending decisions
            if not awaiting_decision:
                if initial_msgs == 2:
                    awaiting_decision = True
                    decision = strat.next_decision()
                    if decision:
                        conn.sendall(pack_client_payload(decision))
                initial_msgs += 1
            else:
                decision = strat.next_decision()
                if decision:
                    conn.sendall(pack_client_payload(decision))
    conn.close()
    return results


def stress_test_server():
    """Runs a comprehensive suite of tests covering both normal edge cases and more
    aggressive stress scenarios. A server instance will be started on a free
    port using run_tcp_server(). Each subtest prints a descriptive label
    alongside the results. The server is not terminated at the end of the
    function; Python's interpreter will exit and clean up daemon threads
    automatically.

    The suite exercises:

      1. Basic edge cases: player bust, dealer bust/tie, multi-round sessions.
      2. Robustness against malformed or partial packets (invalid request and
         decision payloads, truncated payloads).
      3. High-round counts and zero-round requests.
      4. Random strategies to explore diverse game outcomes.
      5. Concurrent clients to ensure the server can handle multiple sessions
         in parallel without crashing.
    """
    # Start the server using a random free port. The accept loop runs on a daemon thread.
    port = run_tcp_server("127.0.0.1", 0, handle_client)
    print(f"[INFO] Started test server on port {port}")

    # Wait briefly to ensure the server thread has started.
    time.sleep(0.2)

    # ---------------------------------------------------------------------------
    # 1. Basic edge cases
    # ---------------------------------------------------------------------------
    # Test 1: Player bust by always hitting.
    bust_result = run_session(port, lambda: AlwaysHit(), rounds=1)
    print("[TEST] Player bust (always hit) result:", bust_result)

    # Test 2: Dealer bust by standing. Run multiple sessions until a win occurs.
    dealer_win = False
    dealer_loss = False
    for _ in range(20):
        result = run_session(port, lambda: AlwaysStand(), rounds=1)
        if result and result[0] == res_win:
            dealer_win = True
            break
        elif result and result[0] == res_loss:
            dealer_loss = True
    print("[TEST] Dealer bust (stand). Win encountered:", dealer_win, "Loss encountered:", dealer_loss)

    # Test 3: Tie detection. Repeat until a tie occurs.
    tie_found = False
    for _ in range(40):
        result = run_session(port, lambda: AlwaysStand(), rounds=1)
        if result and result[0] == res_tie:
            tie_found = True
            break
    print("[TEST] Tie detected:", tie_found)

    # Test 4: Multi-round session with 5 rounds (always stand).
    multi_results = run_session(port, lambda: AlwaysStand(), rounds=5)
    print("[TEST] Multi-round (5) results:", multi_results)

    # ---------------------------------------------------------------------------
    # 2. Malformed packets
    # ---------------------------------------------------------------------------
    # Test 5: Invalid request packet (wrong magic cookie). The server should handle gracefully.
    wrong_cookie_request = b"\x00\x00\x00\x00" + b"\x03" + b"\x01" + b"X" * 32
    s = socket.socket()
    s.connect(("127.0.0.1", port))
    s.sendall(wrong_cookie_request)
    s.close()
    print("[TEST] Sent invalid request with wrong cookie (no crash expected).")

    # Brief pause to allow server to process the invalid request.
    time.sleep(0.2)

    # Test 6: Invalid decision payload (wrong magic cookie in payload). Should trigger server error logging.
    s2 = socket.socket()
    s2.connect(("127.0.0.1", port))
    # Send a valid request first.
    s2.sendall(pack_request(1, "Cheater"))
    # Consume initial three messages from the server.
    for _ in range(3):
        recv_exact(s2, server_payload_len)
    # Send malformed decision payload: wrong cookie.
    invalid_decision = b"\x00\x00\x00\x00" + b"\x04" + b"ABCDE"
    s2.sendall(invalid_decision)
    s2.close()
    print("[TEST] Sent invalid decision payload (watch server logs for CRITICAL error).")

    # Test 7: Truncated decision payload. Send fewer bytes than expected.
    s3 = socket.socket()
    s3.connect(("127.0.0.1", port))
    s3.sendall(pack_request(1, "Trunc"))
    # Consume initial three messages from the server.
    for _ in range(3):
        recv_exact(s3, server_payload_len)
    # Send a truncated payload: only 2 bytes (less than the 9-byte payload)
    s3.sendall(b"\x00\x04")
    s3.close()
    print("[TEST] Sent truncated decision payload (server should handle gracefully).\n")

    # Allow processing time.
    time.sleep(0.2)

    # ---------------------------------------------------------------------------
    # 3. High-round counts and zero-round requests
    # ---------------------------------------------------------------------------
    # Test 8: High number of rounds (e.g. 20). Ensure correct result count.
    high_rounds = 20
    high_results = run_session(port, lambda: AlwaysStand(), rounds=high_rounds)
    print(f"[TEST] High-rounds ({high_rounds}) results length matches:", len(high_results) == high_rounds, "Results:", high_results)

    # Test 9: Zero rounds requested. Expect an empty result list without server crash.
    zero_results = run_session(port, lambda: AlwaysStand(), rounds=0)
    print("[TEST] Zero rounds requested result:", zero_results)

    # ---------------------------------------------------------------------------
    # 4. Random strategies to explore diverse outcomes
    # ---------------------------------------------------------------------------
    import random
    class RandomStrategy:
        """Randomly chooses to hit or stand on the first decision. There is no
        follow-up decision because the server only expects one."""
        def __init__(self):
            self.first = True
        def next_decision(self):
            if not self.first:
                return None
            self.first = False
            return b"Hittt" if random.random() < 0.5 else b"Stand"

    # Run multiple sessions using RandomStrategy to ensure a mix of outcomes occurs and
    # no crashes happen.
    random_results = []
    for _ in range(30):
        result = run_session(port, lambda: RandomStrategy(), rounds=1)
        random_results.append(result[0] if result else None)
    # Count occurrences of each result code
    from collections import Counter
    counts = Counter(random_results)
    print("[TEST] Random strategy distribution:", counts)

    # ---------------------------------------------------------------------------
    # 5. Concurrent sessions
    # ---------------------------------------------------------------------------
    import threading
    concurrent_results = []
    def worker():
        res = run_session(port, lambda: RandomStrategy(), rounds=3)
        concurrent_results.append(res)
    # Launch multiple client threads concurrently
    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("[TEST] Concurrent sessions results:", concurrent_results)


if __name__ == "__main__":
    stress_test_server()