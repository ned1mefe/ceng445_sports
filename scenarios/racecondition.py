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

    sock.recv(4096)  # dump welcome message

    resp = send_cmd(sock, "CREATE_TEAM TestTeam 2020 TUR")
    print("[CREATE_TEAM] ->", resp)

    team_id = re.findall(r"ID:\s*(\S+)", resp)[0]

    resp = send_cmd(sock, "CREATE_TEAM TestTeam2 2020 TUR")
    print("[CREATE_TEAM] ->", resp)

    team2_id = re.findall(r"ID:\s*(\S+)", resp)[0]

    resp = send_cmd(sock, f'CREATE_GAME {team_id} {team2_id} "2025-01-01 10:00"')
    print("[CREATE_GAME] ->", resp)

    game_id = re.findall(r"ID:\s*(\S+)", resp)[0]

    resp = send_cmd(sock, f"START {game_id}")
    print("[START] ->", resp)

    sock.close()
    return team_id, team2_id, game_id

def spam_client(name, game_id, team_id, count):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    sock.recv(4096)  # dump welcome message
    sock.sendall(f"RESPONSE\n".encode())
    sock.sendall(f"USER {name}\n".encode())

    for _ in range(count):
        sock.sendall(f"SCORE {game_id} 1 {team_id}\n".encode())
        #time.sleep(0.001)

    sock.close()
    print(f"{name} finished.")

def print_final_stats(game_id):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    sock.recv(4096)  # dump welcome message

    sock.sendall(f"STATS {game_id}\n".encode())
    data = sock.recv(4096).decode()

    print("\n========== FINAL GAME STATS ==========")
    print(data)
    print("======================================")

    sock.close()


if __name__ == "__main__":
    print("Setting up test entities on server...")
    team_id, team2_id, game_id = setup_test_objects()

    print(f"\nTEAM1 ID  = {team_id}")
    print(f"\nTEAM2 ID  = {team2_id}")
    print(f"GAME ID  = {game_id}")

    TOTAL = 50

    print("\nStarting 2 concurrent clients...")
    t1 = threading.Thread(target=spam_client, args=("ClientA", game_id, team_id, TOTAL))
    t2 = threading.Thread(target=spam_client, args=("ClientB", game_id, team_id, TOTAL))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    print("\nAll clients finished. Fetching STATS...")

    time.sleep(1)
    print_final_stats(game_id)
