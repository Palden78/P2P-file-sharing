import os
import socket
import threading

# Server Configuration
peer_id = "p2"  # Change this for each peer
server_port = 4442  # Change this for each peer
served_files_dir = "served_files"

# Handle client requests
def handle_client(client_socket):
    try:
        request = client_socket.recv(1024).decode("utf-8").strip()
        print(f"Request received: {request}")

        if request.startswith("#FILELIST"):
            files = " ".join(os.listdir(served_files_dir))
            response = f"200 Files served: {files}"
            client_socket.send(response.encode("utf-8"))

        elif request.startswith("#UPLOAD"):
            _, filename = request.split()
            client_socket.send("330 Ready to receive".encode("utf-8"))

            # Receive file
            with open(os.path.join(served_files_dir, filename), "wb") as f:
                while True:
                    data = client_socket.recv(1024)
                    if not data:
                        break
                    f.write(data)
            client_socket.send("200 Upload complete".encode("utf-8"))

        elif request.startswith("#DOWNLOAD"):
            _, filename = request.split()
            filepath = os.path.join(served_files_dir, filename)
            if os.path.exists(filepath):
                client_socket.send("330 Ready to send".encode("utf-8"))
                with open(filepath, "rb") as f:
                    while chunk := f.read(1024):
                        client_socket.send(chunk)
                client_socket.send(b"")  # Signal end of file
            else:
                client_socket.send("250 File not found".encode("utf-8"))
        else:
            client_socket.send("250 Invalid command".encode("utf-8"))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

# Main server loop
def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", server_port))
    server_socket.listen(5)
    print(f"Server {peer_id} listening on port {server_port}...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        threading.Thread(target=handle_client, args=(client_socket,)).start()

if __name__ == "__main__":
    server()