import socket
import time
import re
import ast

HOST = "127.0.0.1"
PORT = 12345

def send_cmd(sock, cmd):
    sock.sendall((cmd + "\n").encode())
    time.sleep(0.1)
    try:
        data = sock.recv(16384).decode()
        return data.strip()
    except socket.timeout:
        return ""
    except Exception as e:
        return f"Error: {e}"

def extract_id(response):
    match = re.search(r"ID:\s*([a-f0-9\-]+)", response)
    if match:
        return match.group(1)
    return None

def parse_stats_time(stats_response):
    try:
        stats_dict = ast.literal_eval(stats_response)
        return stats_dict.get("Time", "Unknown")
    except:
        match = re.search(r"'Time':\s*'([^']+)'", stats_response)
        if match:
            return match.group(1)
        return "Unknown"

def run_time_logic_test():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    sock.recv(4096)  # Clear welcome message

    print("--- [SCENARIO] Game Time Logic & State Test ---")

    print("\n[1] Setting up Teams and Game...")
    
    resp = send_cmd(sock, "CREATE_TEAM TimeTeamA 2024 ITA")
    t1_id = extract_id(resp)
    
    resp = send_cmd(sock, "CREATE_TEAM TimeTeamB 2024 BRA")
    t2_id = extract_id(resp)

    resp = send_cmd(sock, f'CREATE_GAME {t1_id} {t2_id} "2025-01-01 20:00"')
    g_id = extract_id(resp)
    
    if not g_id:
        print("Failed to create game. Exiting.")
        return

    print(f"    Game Created. ID: {g_id}")

    print("\n[2] Starting Game (Waiting 2 seconds)...")
    send_cmd(sock, f"START {g_id}")
    time.sleep(2)

    print("    Action: Team A Scores!")
    send_cmd(sock, f"SCORE {g_id} 1 {t1_id}")
    
    stats = send_cmd(sock, f"STATS {g_id}")
    curr_time = parse_stats_time(stats)
    print(f"    [CHECK] Game Time: {curr_time} (Expected ~00:02)")

    print("\n[3] Pausing Game (Waiting 3 seconds)...")
    send_cmd(sock, f"PAUSE {g_id}")
    
    time.sleep(3) 

    stats = send_cmd(sock, f"STATS {g_id}")
    curr_time = parse_stats_time(stats)
    print(f"    [CHECK] Game Time while Paused: {curr_time}")
    print("    (If logic is correct, this should still be ~00:02, not 00:05)")

    print("\n[4] Resuming Game (Waiting 2 seconds)...")
    send_cmd(sock, f"RESUME {g_id}")
    time.sleep(2)

    print("    Action: Team B Scores!")
    send_cmd(sock, f"SCORE {g_id} 1 {t2_id}")

    stats = send_cmd(sock, f"STATS {g_id}")
    curr_time = parse_stats_time(stats)
    print(f"    [CHECK] Game Time: {curr_time} (Expected ~00:04)")

    print("\n[5] Ending Game...")
    send_cmd(sock, f"END {g_id}")
    
    stats = send_cmd(sock, f"STATS {g_id}")
    curr_time = parse_stats_time(stats)
    
    print("\n--- FINAL REPORT ---")
    print(f"Final Time Status: {curr_time}")
    print("Full Stats Dump:")
    print(stats)
    
    sock.close()

if __name__ == "__main__":
    try:
        run_time_logic_test()
    except KeyboardInterrupt:
        print("\nTest interrupted.")
    except ConnectionRefusedError:
        print("Error: Could not connect to server. Is it running?")