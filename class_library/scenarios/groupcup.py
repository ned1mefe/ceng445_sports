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
        data = sock.recv(65536).decode() 
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

def find_new_games(sock, team_names, known_game_ids):
    resp = send_cmd(sock, "LIST")
    new_games = []
    
    for line in resp.split('\n'):
        if "Game:" in line:
            parts = line.split(': ', 1)
            if len(parts) < 2: continue
            
            gid = parts[0]
            desc = parts[1]
            
            if gid not in known_game_ids:
                if any(name in desc for name in team_names):
                    new_games.append((gid, desc))
    
    return new_games

def run_scenario():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.recv(4096)

    print("--- [SCENARIO] Group Cup: Groups -> Playoffs ---")

    print("\n[1] Creating 8 Teams...")
    team_map = {} # Name -> ID
    
    for i in range(1, 9):
        name = f"GrpTeam{i}"
        tid = create_team(sock, name)
        if tid:
            team_map[name] = tid
            print(f"    Created {name}")
        else:
            print(f"    Error creating {name}")
            return

    
    print("\n[2] Creating Group Cup...")
    cmd = f"CREATE_CUP GROUP 1 {' '.join(team_map.values())}"
    resp = send_cmd(sock, cmd)
    
    cup_id_match = re.search(r"ID:\s*([a-f0-9\-]+)", resp)
    if not cup_id_match:
        print("    Failed to create cup. Response:", resp)
        return
    cup_id = cup_id_match.group(1)
    print(f"    Cup ID: {cup_id}")

    known_games = set()

    
    while True:
        print(f"\n---(Scanning for games) ---")
        time.sleep(1.5)
        
        games = find_new_games(sock, team_map.keys(), known_games)
        
        if not games:
            standings = send_cmd(sock, f"STANDINGS {cup_id}")
           
            if "PlayOffs" in standings:
                print("    No new games found. Tournament appears complete.")
                break
            else:
                time.sleep(2)
                games = find_new_games(sock, team_map.keys(), known_games)
                if not games:
                    print("    No new games found.")
                    break

        print(f"    Found {len(games)} new matches.")

        for gid, desc in games:
            known_games.add(gid)
            
            match_desc = re.search(r"Game:\s+(.*?)\s+vs\s+(.*?)\s+at", desc)
            if not match_desc:
                print(f"    Skipping unparsable game: {desc}")
                continue
            
            home_name = match_desc.group(1)
            away_name = match_desc.group(2)
            
    
            hid = team_map.get(home_name)
            aid = team_map.get(away_name)
            
            print(f"    > Match: {home_name} vs {away_name}")
            
            send_cmd(sock, f"START {gid}")
            
            score_h = random.randint(0, 5)
            score_a = random.randint(0, 5)
            
            if hid: send_cmd(sock, f"SCORE {gid} {score_h} {hid}")
            if aid: send_cmd(sock, f"SCORE {gid} {score_a} {aid}")
            
            print(f"      Final: {home_name} {score_h} - {score_a} {away_name}")
            
            send_cmd(sock, f"END {gid}")
        

    # 4. Final Results
    print("\n[4] Tournament Finished. Final Standings:")
    print(send_cmd(sock, f"STANDINGS {cup_id}"))
    
    sock.close()

if __name__ == "__main__":
    run_scenario()