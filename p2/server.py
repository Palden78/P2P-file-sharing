import os
import socket
import threading
import sys
import time

# Name of directory containing served files
servedFilesDirectory = "served_files"

# Set containing active file uploads
active_file_uploads = set()


class ServerThread(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client
    def run(self):
        handle_client(self.client)

class ServerMain:
    def run_server(self):
        serverPort = server_port_number
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind(("localhost", server_port_number))
        serverSocket.listen(5)
        print(f"Server {peer_ID} is now listening on port {serverPort}..")

        while True:
            client_socket, addr = serverSocket.accept()
            print(f"Connection from {addr}")
            t = ServerThread(client_socket)
            t.start()

def FILELIST_SERVER(client_socket):
    filesServed = " ".join(os.listdir(servedFilesDirectory))
    responseMessage = f"200 Files served: {filesServed}"
    print(responseMessage)
    client_socket.send(responseMessage.encode("utf-8"))

def UPLOAD_SERVER(client_socket, request):
    print("Entered upload function")
    _, filename, _, file_size = request.split()
    filepath = os.path.join(servedFilesDirectory, filename)
    if filename in active_file_uploads:
        response = f"250 Currently receiving file {filename}"
    elif os.path.exists(filepath):
        response = f"250 Already serving file {filename}"
    else:
        response = f"330 Ready to receive file {filename}"
        active_file_uploads.add(filename)  # Mark upload as active
    
    print(response)

    #Send the response to the client
    client_socket.send(response.encode("utf-8"))

    if response.startswith("330"):
        with open(filepath, "wb") as file:
            while True:
                chunkRequest = client_socket.recv(1024).decode("utf-8")
                if chunkRequest.startswith("#UPLOAD"):
                    _, filename, chunkID, chunkData = chunkRequest.split(" ",4)
                    file.write(chunkData.encode('utf-8'))
                    client_socket.send(f"200 File {filename} chunk {chunkID} received".encode('utf-8'))
                elif chunkRequest == "UPLOAD_COMPLETE":
                    break
            
        active_file_uploads.remove(filename)
        client_socket.send(f"200 File {filename} received".encode('utf-8'))


def handle_client(client_socket):
    try:
        clientRequest = client_socket.recv(1024).decode("utf-8").strip()
        print(f"Client Request received: {clientRequest}")

        if clientRequest.startswith("#FILELIST"):
            FILELIST_SERVER(client_socket)
        elif clientRequest.startswith("#UPLOAD"):
            UPLOAD_SERVER(client_socket, clientRequest)
        elif len(clientRequest) == 0:
            raise Exception("Client closed connection")
    except Exception as e:
        print(e)
    finally:
        client_socket.close()

def getServerPortNumber(peerID):
    with open("../peer_settings.txt", "r") as file:
        for Line in file:
            peer_id, ip, port = Line.strip().split()
            if peer_id == peerID:
                return int(port)

if __name__ == "__main__":
    peer_ID= sys.argv[-1]
    print(peer_ID)

    server_port_number = getServerPortNumber(peer_ID)
    print(server_port_number)

    server = ServerMain()
    server.run_server()