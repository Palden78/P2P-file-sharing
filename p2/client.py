import os
import socket

# Load peer settings
def load_peer_settings():
    peer_settings = {}
    with open("../peer_settings.txt", "r") as f:
        for line in f:
            peer_id, ip, port = line.strip().split()
            peer_settings[peer_id] = (ip, int(port))
    return peer_settings

peer_settings = load_peer_settings()

# Send request to a peer
def send_request(peer_id, request):
    if peer_id not in peer_settings:
        print(f"Peer {peer_id} not found in settings.")
        return

    ip, port = peer_settings[peer_id]
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))
            s.send(request.encode("utf-8"))
            response = s.recv(4096).decode("utf-8")
            print(response)
    except Exception as e:
        print(f"Error communicating with {peer_id}: {e}")

# #FILELIST command
def filelist(peers):
    for peer_id in peers:
        request = "#FILELIST"
        send_request(peer_id, request)

# #UPLOAD command
def upload(filename, peers):
    filepath = os.path.join("served_files", filename)
    if not os.path.exists(filepath):
        print(f"Peer does not serve file {filename}")
        return

    for peer_id in peers:
        try:
            ip, port = peer_settings[peer_id]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip, port))
                s.send(f"#UPLOAD {filename}".encode("utf-8"))
                response = s.recv(1024).decode("utf-8")
                print(response)

                if "330 Ready to receive" in response:
                    with open(filepath, "rb") as f:
                        while chunk := f.read(1024):
                            s.send(chunk)
                    s.send(b"")  # Signal end of file
                    print(s.recv(1024).decode("utf-8"))
        except Exception as e:
            print(f"Error uploading to {peer_id}: {e}")

# #DOWNLOAD command
def download(filename, peer_id):
    try:
        ip, port = peer_settings[peer_id]
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))
            s.send(f"#DOWNLOAD {filename}".encode("utf-8"))
            response = s.recv(1024).decode("utf-8")
            print(response)

            if "330 Ready to send" in response:
                with open(os.path.join("served_files", filename), "wb") as f:
                    while True:
                        data = s.recv(1024)
                        if not data:
                            break
                        f.write(data)
                print("Download complete.")
            else:
                print(response)
    except Exception as e:
        print(f"Error downloading from {peer_id}: {e}")

# Main client loop
if __name__ == "__main__":
    while True:
        command = input("Enter command: ").strip()
        if command.startswith("#FILELIST"):
            _, *peers = command.split()
            filelist(peers)
        elif command.startswith("#UPLOAD"):
            _, filename, *peers = command.split()
            upload(filename, peers)
        elif command.startswith("#DOWNLOAD"):
            _, filename, peer_id = command.split()
            download(filename, peer_id)
        else:
            print("Invalid command.")