import socket
import re
import time
import random
import sys

HOST = "127.0.0.1"
PORT = 12345

def send_cmd(sock, cmd):
    """Sends a command to the server and returns the response."""
    sock.sendall((cmd + "\n").encode())
    # Give the server a moment to process/flush
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

def find_league_games(sock, team_names):
    """
    Retrieves Game IDs for the League. Since LeagueCup schedules all games
    at initialization, we can fetch them all at once by filtering the LIST
    for matches involving our teams.
    """
    resp = send_cmd(sock, "LIST")
    league_games = []
    
    # Parse lines like: "uuid: Game: TeamA vs TeamB at ..."
    for line in resp.split('\n'):
        if "Game:" in line:
            parts = line.split(': ', 1)
            if len(parts) < 2: continue
            
            gid = parts[0]
            desc = parts[1]
            
            # Check if this game involves our teams
            if any(name in desc for name in team_names):
                league_games.append((gid, desc))
    
    return league_games

def run_scenario():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.recv(4096) # Welcome message

    print("--- [SCENARIO] League Cup: Round Robin ---")

    # 1. Create 4 Teams (Round Robin = 6 games total)
    print("\n[1] Creating 4 Teams...")
    team_map = {} # Name -> ID
    team_ids = []
    
    for i in range(1, 5):
        name = f"LeagueTeam{i}"
        tid = create_team(sock, name)
        if tid:
            team_map[name] = tid
            team_ids.append(tid)
            print(f"    Created {name}")
        else:
            print(f"    Error creating {name}")
            return

    # 2. Create Cup
    print("\n[2] Creating League Cup...")
    # LEAGUE type creates a round-robin schedule
    cmd = f"CREATE_CUP LEAGUE 1 {' '.join(team_ids)}"
    resp = send_cmd(sock, cmd)
    cup_id_match = re.search(r"ID:\s*([a-f0-9\-]+)", resp)
    
    if not cup_id_match:
        print("    Failed to create cup.")
        return
    cup_id = cup_id_match.group(1)
    print(f"    Cup ID: {cup_id}")

    # 3. Retrieve Games
    # In League Cup, all games are created immediately.
    print("\n[3] Retrieving Schedule...")
    games = find_league_games(sock, team_map.keys())
    
    if not games:
        print("    No games found. Something went wrong.")
        return

    print(f"    Scheduled {len(games)} matches for the season.")
    
    # Shuffle execution order to simulate concurrent matches happening over time
    random.shuffle(games)

    # 4. Play Season
    print("\n[4] Playing Season...")
    
    for i, (gid, desc) in enumerate(games, 1):
        # Identify teams from description
        match_desc = re.search(r"Game:\s+(.*?)\s+vs\s+(.*?)\s+at", desc)
        if not match_desc:
            print(f"    Could not parse: {desc}")
            continue
        
        home_name = match_desc.group(1)
        away_name = match_desc.group(2)
        
        print(f"    [{i}/{len(games)}] Match: {home_name} vs {away_name}")
        
        # Start Game
        send_cmd(sock, f"START {gid}")
        
        # Random Scores
        score_h = random.randint(0, 4)
        score_a = random.randint(0, 4)
        
        # Get IDs to score
        hid = team_map.get(home_name)
        aid = team_map.get(away_name)
        
        if hid: send_cmd(sock, f"SCORE {gid} {score_h} {hid}")
        if aid: send_cmd(sock, f"SCORE {gid} {score_a} {aid}")
        
        print(f"        Result: {home_name} {score_h} - {score_a} {away_name}")
        
        # End Game
        send_cmd(sock, f"END {gid}")
        
        # Optional: Print standings every few games to show progress
        if i % 2 == 0:
            print("        Updating League Table...")

    # 5. Final Results
    print("\n[5] Season Finished. Final Standings:")
    standings = send_cmd(sock, f"STANDINGS {cup_id}")
    print(standings)
    
    sock.close()

if __name__ == "__main__":
    run_scenario()