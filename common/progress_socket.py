import socket
import json
import threading
import logging
from typing import Dict, Any

logger = logging.getLogger('contactmailer')

HOST = '127.0.0.1'
PORT = 65432

class ProgressServer:
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.running = False
        self.server_socket = None
        self.clients = []
        self.lock = threading.Lock()
        
    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"[Server] Progress server listening on {self.host}:{self.port}")
        
        while self.running:
            try:
                self.server_socket.settimeout(1.0)
                conn, addr = self.server_socket.accept()
                with self.lock:
                    self.clients.append(conn)
                client_thread = threading.Thread(target=self._handle_client, args=(conn,), daemon=True)
                client_thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"[Server] Error accepting connection: {e}")

    def _handle_client(self, conn):
        with conn:
            buffer = ""
            while True:
                try:
                    data = conn.recv(1024)
                    if not data:
                        break
                    buffer += data.decode('utf-8')
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if line.strip():
                            # It's an update from a worker
                            self._broadcast(line.strip())
                except Exception as e:
                    break
        with self.lock:
            if conn in self.clients:
                self.clients.remove(conn)

    def _broadcast(self, message: str):
        print(f"[Broadcast] {message}")
        msg_encoded = (message + "\n").encode('utf-8')
        with self.lock:
            for c in list(self.clients):
                try:
                    c.sendall(msg_encoded)
                except:
                    self.clients.remove(c)

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()

def send_progress_update(campaign_id: str, sent: int, failed: int, total: int):
    try:
        data = {
            "campaign_id": str(campaign_id),
            "status": "in_progress",
            "sent": sent,
            "failed": failed,
            "total": total
        }
        message = json.dumps(data) + "\n"
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2.0)
            s.connect((HOST, PORT))
            s.sendall(message.encode('utf-8'))
    except Exception as e:
        logger.error(f"Failed to send progress update: {e}")

def run_server():
    server = ProgressServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

def run_client():
    print(f"Connecting to Progress Server at {HOST}:{PORT}")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            print("Connected. Waiting for progress updates...")
            while True:
                data = s.recv(1024)
                if not data:
                    print("Connection closed by server.")
                    break
                print(f"Progress: {data.decode('utf-8').strip()}")
    except ConnectionRefusedError:
        print("Could not connect. Is the server running?")
    except KeyboardInterrupt:
        print("Exiting client.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "client":
        run_client()
    else:
        run_server()
