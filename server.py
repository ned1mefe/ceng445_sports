import threading
import pickle
import os
import sys
from websockets.sync import server
from session import Session
from class_library.catalog import Catalog

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


def agent(wsock):
    """
    WebSocket agent handling a single client connection.
    This function is called by the server for each new connection.
    """
    addr = wsock.remote_address
    print(f"Connection accepted from {addr}")

    # Create a session handler for this connection
    session = Session(
        wsock=wsock,
        addr=addr,
        catalog=catalog,
        catalog_lock=catalog_lock,
        datafile=DATA_FILE
    )

    session.run()


if __name__ == "__main__":
    load_state()

    print(f"WebSocket Server running on {HOST}:{PORT}")

    try:
        with server.serve(agent, HOST, PORT) as srv:
            srv.serve_forever()

    except KeyboardInterrupt:
        print("\nServer stopping...")
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        save_state_on_exit()
        sys.exit(0)
