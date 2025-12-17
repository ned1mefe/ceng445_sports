import socket
import threading
import pickle
import os
import sys
from session import Session
from catalog import Catalog

HOST = '0.0.0.0'
PORT = 12345
catalog = None
catalog_lock = threading.RLock()
DATA_FILE = "server_state.pkl"

def load_state():
    global catalog
    if os.path.exists(DATA_FILE):
        print(f"Loading state from {DATA_FILE}...")
        try:
            with open(DATA_FILE, 'rb') as f:
                catalog = pickle.load(f)

        except Exception as e:
            print(f"Error loading state: {e}")
            print("Starting with a fresh catalog.")
            catalog = Catalog()
    else:
        print("No saved state found. Starting fresh.")
        catalog = Catalog()

def save_state_on_exit():
    print("Saving state before shutdown...")
    with catalog_lock:
        with open(DATA_FILE, 'wb') as f:
            pickle.dump(catalog, f)
    print("State saved.")

if __name__ == "__main__":
    load_state()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Allow immediate reuse of the port (prevents "Address already in use" errors after restart)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(10)

        print(f"Server running on {HOST}:{PORT}")

        while True:
            client_sock, addr = server_socket.accept()
            print(f"Connection accepted from {addr}")

            session_thread = Session(
                sock=client_sock, 
                addr=addr,
                catalog=catalog,
                catalog_lock=catalog_lock,
                datafile=DATA_FILE
            )
            session_thread.daemon = True # when server exits, threads exit too
            session_thread.start()

    except KeyboardInterrupt:
        print("\nServer stopping...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        save_state_on_exit()
        server_socket.close()
        sys.exit(0)