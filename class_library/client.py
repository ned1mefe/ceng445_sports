import socket
import threading
import sys

HOST = '127.0.0.1'
PORT = 12345

def receive_messages(sock):
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("\n Server broke the connection.")
                break
            print(data.decode('utf-8'), end='')
        except OSError:
            break
        except Exception as e:
            print("Error:" + e)
            break

try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))
    print(f"Connected to {HOST}:{PORT} address. ")
    print("-" * 30)

    listen_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    listen_thread.daemon = True
    listen_thread.start()

    while True:
        msg = input() 
        client_socket.sendall((msg + "\n").encode('utf-8'))

except KeyboardInterrupt:
    print("\nQuitting...")
except ConnectionRefusedError:
    print("Error, server not running.")
finally:
    client_socket.close()