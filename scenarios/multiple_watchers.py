import socket
import threading
import time
import re

HOST = "127.0.0.1"
PORT = 12345

def send_cmd(sock, cmd):
    sock.sendall((cmd + "\n").encode())
    data = sock.recv(4096).decode()
    return data.strip()

def setup_test_objects():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.recv(4096)

    print("[SETUP] Creating teams and games...")

    # --- Game 1 Setup ---
    resp = send_cmd(sock, "CREATE_TEAM TeamA 2020 TUR")
    t1_id = re.findall(r"ID:\s*(\S+)", resp)[0]
    
    resp = send_cmd(sock, "CREATE_TEAM TeamB 2020 USA")
    t2_id = re.findall(r"ID:\s*(\S+)", resp)[0]

    resp = send_cmd(sock, f'CREATE_GAME {t1_id} {t2_id} "2025-01-01 10:00"')
    g1_id = re.findall(r"ID:\s*(\S+)", resp)[0]
    
    # --- Game 2 Setup ---
    resp = send_cmd(sock, "CREATE_TEAM TeamC 2020 GER")
    t3_id = re.findall(r"ID:\s*(\S+)", resp)[0]
    
    resp = send_cmd(sock, "CREATE_TEAM TeamD 2020 FRA")
    t4_id = re.findall(r"ID:\s*(\S+)", resp)[0]

    resp = send_cmd(sock, f'CREATE_GAME {t3_id} {t4_id} "2025-01-01 12:00"')
    g2_id = re.findall(r"ID:\s*(\S+)", resp)[0]

    # Start both games so scoring is allowed
    send_cmd(sock, f"START {g1_id}")
    send_cmd(sock, f"START {g2_id}")

    sock.close()
    return (g1_id, t1_id), (g2_id, t3_id)

def watcher_client(name, game_ids, duration=6):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.recv(4096) # Welcome msg

    sock.sendall(f"USER {name}\n".encode())
    sock.recv(1024)

    print(f"[{name}] Sending WATCH commands for {game_ids}...")
    
    for gid in game_ids:
        sock.sendall(f"WATCH {gid}\n".encode())
        sock.recv(1024)

    print(f"[{name}] Listening... (Should ONLY see updates for {game_ids})")
    
    sock.settimeout(10.0)
    
    while True:
        try:
            data = sock.recv(4096).decode()
            if data:
                lines = data.split('\n')
                for line in lines:
                    if line.strip():
                        print(f"   >>> [{name} NOTIFICATION] {line.strip()}")
        except socket.timeout:
            break
        except Exception as e:
            print(f"[{name}] Connection closed or error: {e}")
            break

    sock.close()
    print(f"[{name}] Finished watching.")

def scorer_client(name, game_id, team_id, count, delay=0):
    time.sleep(delay) 
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.recv(4096)

    sock.sendall(f"USER {name}\n".encode())
    sock.recv(1024)

    print(f"[{name}] Updating Game {game_id}...")

    for i in range(count):
        sock.sendall(f"SCORE {game_id} 1 {team_id}\n".encode())
        sock.recv(1024) 
        time.sleep(0.5)

    sock.close()
    print(f"[{name}] Finished updates.")

if __name__ == "__main__":
    print("Setting up 2 concurrent matches on server...")
    (g1_id, t1_id), (g2_id, t3_id) = setup_test_objects()

    print(f"\nGAME 1 ID = {g1_id}")
    print(f"GAME 2 ID = {g2_id}")
    print("-" * 50)
    COUNT = 3

    watcher_a = threading.Thread(target=watcher_client, args=("WatcherA(G1)", [g1_id], 6))
    watcher_b = threading.Thread(target=watcher_client, args=("WatcherB(G2)", [g2_id], 6))
    
    scorer_a = threading.Thread(target=scorer_client, args=("ScorerA", g1_id, t1_id, COUNT, 1))
    scorer_b = threading.Thread(target=scorer_client, args=("ScorerB", g2_id, t3_id, COUNT, 1))

    watcher_a.start()
    watcher_b.start()
    scorer_a.start()
    scorer_b.start()

    watcher_a.join()
    watcher_b.join()
    scorer_a.join()
    scorer_b.join()
    
    print("\nScenario finished.")