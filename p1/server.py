import os
import socket
import threading

# Name of directory containing served files
servedFilesDirectory = "served_files"

peer_ID = "p1"
server_port_number = 4441

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


def handle_client(client_socket):
    try:
        clientRequest = client_socket.recv(1024).decode("utf-8").strip()
        print(f"Client Request received: {clientRequest}")

        if clientRequest.startswith("#FILELIST"):
            FILELIST_SERVER(client_socket)
    
    except Exception as e:
        print("error")
    finally:
        client_socket.close()



if __name__ == "__main__":
    server = ServerMain()
    server.run_server()

    
