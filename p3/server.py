import os
import socket
import threading
import sys
import time

# Name of directory containing served files
servedFilesDirectory = "served_files"

# Set containing active file uploads
active_file_uploads = set()


def GetFileSize(Filename):
    #Function to get Size of File based on filename
    size = os.path.getsize(f'served_files/{Filename}')
    return size


class ServerThread(threading.Thread):
    def __init__(self, client):
        threading.Thread.__init__(self)
        self.client = client
    
    def FILELIST_SERVER(self,client_socket):
        print("Entered filelist function")
        #Function to handle #FILELIST request from client
        filesServed = " ".join(os.listdir(servedFilesDirectory))
        responseMessage = f"200 Files served: {filesServed}"
        print(responseMessage)
        client_socket.send(responseMessage.encode("utf-8"))

    def UPLOAD_SERVER(self, client_socket, request):
        print("Entered upload function")
        #Function to handle #UPLOAD request from client
        _, filename, _, file_size = request.split()
        filepath = os.path.join(servedFilesDirectory, filename)

        #Handle different cases during upload
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
                        _, filename, chunk, chunkID, chunkData = chunkRequest.split(" ",4)
                        file.write(chunkData.encode('utf-8'))
                        client_socket.send(f"200 File {filename} chunk {chunkID} received".encode('utf-8'))
                    elif chunkRequest == "UPLOAD_COMPLETE":
                        break
                    elif len(chunkRequest) == 0:
                        #The client has disconnected during upload, upload is incomplete
                        try:
                            os.remove(filepath)
                            active_file_uploads.remove(filename)
                            print(f"Removed unfinished file: {filepath}")
                        except OSError as e:
                            print(f"Error removing file: {e}")
                        raise Exception("Client closed connection")

            #Remove the file from the active file uploads set
            active_file_uploads.remove(filename)
            client_socket.send(f"200 File {filename} received".encode('utf-8'))
    
    def DOWNLOAD_SERVER_INITIAL_CHECK(self, client_socket, request):
        print("Entered Download check function")
        #Function to handle phase 1 #DOWNLOAD request from client
        _, filename = request.split()
        filepath = os.path.join(servedFilesDirectory, filename)

        if filename in active_file_uploads:
            #The file the client wants to download is currently being uploaded to the server
            response = f"250 Currently receiving file {filename}"
        elif os.path.exists(filepath):
            #The file requested by the client is being served by the server
            SizeOfFile = GetFileSize(filename)
            response = f"330 Ready to send {filename} bytes {SizeOfFile}"
        else:
            #The file requested by the client is not being served by the server
            response = f"250 Not serving file {filename}"

        print(response)

        client_socket.send(response.encode("utf-8"))

    def HANDLE_DOWNLOAD_CHUNK_REQUEST(self, client_socket, filename, chunk_ID):
        print("Entered Handle Download chunk request function")
        #Function to handle phase 2 #DOWNLOAD request from client
        filepath = os.path.join(servedFilesDirectory, filename)
        chunkSize = 100

        try:
            with open(filepath, 'rb') as file:
                file.seek(chunk_ID * chunkSize)
                chunkData = file.read(chunkSize)
                response = f"200 File {filename} chunk {chunk_ID} {chunkData.decode('utf-8', errors='ignore')}"
                client_socket.send(response.encode('utf-8'))
        except Exception as e:
            print(f"Error reading chunk {chunk_ID} from file {filename}: {e}")
            client_socket.send(f"250 Error reading chunk {chunk_ID}".encode("utf-8"))
        

    def run(self):
        client_socket = self.client
        try:
            clientRequest = client_socket.recv(1024).decode("utf-8").strip()
            print(f"Client Request received: {clientRequest}")

            if clientRequest.startswith("#FILELIST"):
                self.FILELIST_SERVER(client_socket)
            elif clientRequest.startswith("#UPLOAD"):
                self.UPLOAD_SERVER(client_socket, clientRequest)
            elif clientRequest.startswith("#DOWNLOAD"):
                parts = clientRequest.split()
                command = parts[0]
                filename = parts[1]

                if len(parts) == 2:
                    #Initial #DOWNLOAD request sent by client for checking
                    self.DOWNLOAD_SERVER_INITIAL_CHECK(client_socket,clientRequest)
                elif len(parts) == 4 and parts[2] == "chunk":
                    #Client requests a chunk from the server
                    chunk_ID = int(parts[3])
                    self.HANDLE_DOWNLOAD_CHUNK_REQUEST(client_socket, filename, chunk_ID)

        except Exception as e:
            print(e)
        finally:
            self.client.close()
    

class ServerMain:
    def run_server(self):
        serverPort = server_port_number
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        #Bind the port number, ip to the Server socket and listen for incoming client connections
        serverSocket.bind(("localhost", server_port_number))
        serverSocket.listen()

        print(f"Server {peer_ID} is now listening on port {serverPort}..")

        #Create an array called threads to store threads
        threads = []

        try:
            #Continuously accept new connections from clients and create a new thread to handle it
            while True:
                client_socket, addr = serverSocket.accept()
                print(f"Connection from {addr}")
                thread = ServerThread(client_socket)
                thread.start()
                threads.append(thread)

        except KeyboardInterrupt:
            print("Server is shutting down.")

        finally:
            serverSocket.close()
            print("Server socket closed.")

            # Join all threads before exiting
            for thread in threads:
                if thread.is_alive():
                    thread.client.close()
                thread.join()


def getServerPortNumber(peerID):
    #Function used to get the Port number of the server

    #Get the filepath of peer_settings.txt file 
    file_path = os.path.join("..", "peer_settings.txt")
    with open(file_path, "r") as file:
        for Line in file:
            peer_id, ip, port = Line.strip().split()
            if peer_id == peerID:
                return int(port)


if __name__ == "__main__":
    #get the peer_ID of the server from the last arg in the command line
    peer_ID= sys.argv[-1]

    #Print the peer_ID (Testing purposes)
    print(peer_ID)

    #Based on the peer_ID get the correct port number of the server
    server_port_number = getServerPortNumber(peer_ID)

    #Print the server_port_number (Testing purposes)
    print(server_port_number)

    #Create an instance of the server main class and run the server
    server = ServerMain()
    server.run_server()