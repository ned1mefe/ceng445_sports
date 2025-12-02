import socket
import re
import time
import random
import sys

HOST = "127.0.0.1"
PORT = 12345

def send_cmd(sock, cmd):
    sock.sendall((cmd + "\n").encode())
    time.sleep(0.05)
    try:
        data = sock.recv(16384).decode()
        return data.strip()
    except socket.timeout:
        return ""
    except Exception:
        return ""

def create_team(sock, name):
    resp = send_cmd(sock, f"CREATE_TEAM {name} 2024 Int")
    match = re.search(r"ID:\s*([a-f0-9\-]+)", resp)
    if match:
        return match.group(1)
    return None

def find_new_round_games(sock, team_names, known_game_ids):
    resp = send_cmd(sock, "LIST") # we have to list new games because we do not know their IDs yet
    new_games = []

    for line in resp.split('\n'):
        if "Game:" in line:
            parts = line.split(': ', 1)
            if len(parts) < 2: continue
            
            gid = parts[0]
            desc = parts[1]
            
            # Check if this game involves our teams and is new
            if gid not in known_game_ids:
                if any(name in desc for name in team_names):
                    new_games.append((gid, desc))
    
    return new_games

def run_scenario():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.recv(4096) 

    print("--- [SCENARIO] Elimination Cup: Random Scoring until Winner ---")

    print("\n[1] Creating 8 Teams...")
    team_map = {} # Name -> ID
    team_ids = []
    
    for i in range(1, 9):
        name = f"ElimTeam{i}"
        tid = create_team(sock, name)
        if tid:
            team_map[name] = tid
            team_ids.append(tid)
            print(f"    Created {name}")
        else:
            print(f"    Error creating {name}")
            return

    # 2. Create Cup
    print("\n[2] Creating Elimination Cup...")
    cmd = f"CREATE_CUP ELIMINATION 1 {' '.join(team_ids)}"
    resp = send_cmd(sock, cmd)
    cup_id_match = re.search(r"ID:\s*([a-f0-9\-]+)", resp)
    
    if not cup_id_match:
        print("    Failed to create cup.")
        return
    cup_id = cup_id_match.group(1)
    print(f"    Cup ID: {cup_id}")

    # Watch cup to receive end notifications (optional for logic, good for logging)
    send_cmd(sock, f"WATCH {cup_id}")

    # 3. Game Loop
    known_games = set()
    round_num = 1
    
    while True:
        # Check if we have a winner first (standings returns specific structure)
        standings = send_cmd(sock, f"STANDINGS {cup_id}")

        print(f"\n--- Round {round_num} ---")
        
        # Get IDs for the games just created by the Cup
        games = find_new_round_games(sock, team_map.keys(), known_games)
        
        if not games:
            # No new games found. Cup might be over.
            print("    No new games found. Checking results...")
            print(f"\n[FINAL STANDINGS]\n{standings}")
            break
            
        print(f"    Found {len(games)} matches.")

        for gid, desc in games:
            known_games.add(gid)
            
            # Identify teams from description "Game: TeamA vs TeamB at..."
            # Regex to pull names out
            match_desc = re.search(r"Game:\s+(.*?)\s+vs\s+(.*?)\s+at", desc)
            if not match_desc:
                print(f"    Could not parse: {desc}")
                continue
            
            home_name = match_desc.group(1)
            away_name = match_desc.group(2)
            
            print(f"    > Playing: {home_name} vs {away_name} (ID: {gid})")
            
            # Start Game
            send_cmd(sock, f"START {gid}")
            
            # Random Scores
            score_h = random.randint(0, 5)
            score_a = random.randint(0, 5)
            
            # We need Team IDs to score. Use our map.
            hid = team_map.get(home_name)
            aid = team_map.get(away_name)
            
            if hid: send_cmd(sock, f"SCORE {gid} {score_h} {hid}")
            if aid: send_cmd(sock, f"SCORE {gid} {score_a} {aid}")
            
            print(f"      Result: {home_name} {score_h} - {score_a} {away_name}")
            
            send_cmd(sock, f"END {gid}")
        
        time.sleep(1)
        round_num += 1

    sock.close()

if __name__ == "__main__":
    run_scenario()