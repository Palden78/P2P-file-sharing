import os
import socket
import threading
import time
import sys

#Function to load peer settings info
def LoadPeerSettingsFile():
    #Create a dictionary to store peer settings
    peer_settings = dict()

    #Read from peer_settings.txt file
    with open("../peer_settings.txt", "r") as file:
        for Line in file:
            peer_id , ipAddr, portNum = Line.strip().split()
            #Key value pair of peer id and info is created
            peer_settings[peer_id] = (ipAddr, int(portNum))
    
    #Return the peer_settings dictionary 
    return peer_settings

#Global variable containing dictionary of peer and its information
peer_settings = LoadPeerSettingsFile()


def FilesServedByClient():
    #Function to get the list of files served by client
    #Based on the served_files directory of client
    Files = []
    for filename in os.listdir('served_files'):
        Files.append(filename)
    return Files

def GetFileSize(Filename):
    #Function to get Size of File based on filename
    size = os.path.getsize(f'served_files/{Filename}')
    return size

def GetNumberOfChunks(Filesize):
    chunkSize = 100
    fullChunks = Filesize // chunkSize

    if Filesize % chunkSize >0:
        fullChunks += 1
    
    return fullChunks



class ClientThread(threading.Thread):
    def __init__(self, target, *args):
        threading.Thread.__init__(self)
        self.target = target
        self.args = args
    def run(self):
        self.target(*self.args)

class ClientMain:
    def __init__(self):
        self.LocalPeerID = os.path.basename(os.getcwd())

    #Function to send request to a peer
    def SendFileListRequest(self,Peer_Id, Request):

        #The peer is not a known peer in peer_settings
        if Peer_Id not in peer_settings:
            return
        
        #The peer is a known peer in peer_settings
        #Get the IP and PortNum of the peer
        ip, PortNum = peer_settings[Peer_Id]

        #Try connecting to the server of the specified peer
        try:
            #Connect using socket with the ip and port number of the peer
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((ip,PortNum))
                sock.send(Request.encode("utf-8"))
                #Print the sent request in terminal
                print(f"Client ({Peer_Id}): {Request}")
                response_msg = sock.recv(1024) .decode("utf-8")
                print(f"Server ({Peer_Id}): {response_msg}")
                return response_msg
        except Exception as ex:
            print(f"TCP connection to {Peer_Id} has failed: {ex}")
        finally:
            #close the socket
            sock.close()
    
    #Function to send Upload request to a peer
    def SendUploadRequest(self,Peer_Id, Request,filepath, Filename):

        #The peer is not a known peer in peer_settings
        if Peer_Id not in peer_settings:
            return
        
        #The peer is a known peer in peer_settings
        #Get the IP and PortNum of the peer
        ip, PortNum = peer_settings[Peer_Id]

        #Try connecting to the server of the specified peer
        try:
            #Connect using socket with the ip and port number of the peer
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((ip,PortNum))
                print(f"Uploading file {Filename}")
                sock.send(Request.encode("utf-8"))
                #Print the sent request in terminal
                print(f"Client ({Peer_Id}): {Request}")
                response_msg = sock.recv(1024) .decode("utf-8")
                print(f"Server ({Peer_Id}): {response_msg}")
                time.sleep(0.5)

                if response_msg.startswith("330"):
                    with open(filepath, "rb") as f:
                        chunk_id = 0
                        while chunk := f.read(100):
                            chunkRequest = f"#UPLOAD {Filename} chunk {chunk_id} {chunk.decode('utf-8')}"
                            sock.send(chunkRequest.encode('utf-8'))
                            command, filename, chunk, chunkID, chunkData = chunkRequest.split(" ",4)
                            print(f"Client ({Peer_Id}): {command} {filename} {chunk} {chunkID}")

                            chunkResponse = sock.recv(1024).decode('utf-8')
                            if len(chunkResponse) == 0:
                                raise Exception("Server closed connection")

                            print(f"Server ({Peer_Id}): {chunkResponse}")
                            time.sleep(0.5)

                            chunk_id +=1
                        
                        sock.send("UPLOAD_COMPLETE".encode('utf-8'))
                        completion_response = sock.recv(1024).decode('utf-8')
                    if completion_response and "200 File" in completion_response:
                        print(f"File {Filename} upload success to {Peer_Id}")
                    else:
                        print(f"File {Filename} upload failed to {Peer_Id}")  
        except KeyboardInterrupt:
            print("KEYBOARD INTREEUPT")
        except Exception as ex:
            print(f"TCP connection to {Peer_Id} has failed: {ex}")
            print(f"File {Filename} upload failed to {Peer_Id}")
        finally:
            #close the socket
            sock.close()
    
    def SendDownloadRequest(self,Peer_Id, Request, Filename, initialRequest = True):
        if Peer_Id not in peer_settings:
            return
        
        ip, PortNum = peer_settings[Peer_Id]

        try:
            #Connect using socket with the ip and port number of the peer
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((ip,PortNum))
                sock.send(Request.encode("utf-8"))
                print(f"Client ({Peer_Id}): {Request}")
                response_msg = sock.recv(1024) .decode("utf-8")
                if initialRequest:
                    print(f"Server ({Peer_Id}): {response_msg}")
                else:
                    responseCode, File, fileName, chunk, chunkid, chunkData = response_msg.split(" ", 5)
                    print(f"Server ({Peer_Id}): {responseCode} {File} {fileName} {chunk} {chunkid}")
                time.sleep(0.5)
                return response_msg
        except Exception as ex:
            print(f"TCP connection to {Peer_Id} has failed: {ex}")
            print(f"File {Filename} download failed")
        finally:
            #close the socket
            sock.close()
    
    def FILELIST(self, Peers):
        #Request to be sent
        Request = "#FILELIST"
        threads = []
        for Peer_Id in Peers:
            thread = ClientThread(self.SendFileListRequest, Peer_Id, Request)
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()
    
    def UPLOAD(self,Filename, Peers, currentClient):
        #Call the function to get the list of files served by current client
        FilesServed = FilesServedByClient()

        #File path for the file to be uploaded
        filepath = os.path.join("served_files", Filename)

        #If the peer does not have the file to upload
        if Filename not in FilesServed:
            print(f"Peer {currentClient} does not serve file {Filename}")
            return
        
        #The peer has the file to upload
        SizeOfFile = GetFileSize(Filename)
        Request = f"#UPLOAD {Filename} bytes {SizeOfFile}"

        threads = []

        for Peer_Id in Peers:
            #Send the request to the respective peer
            thread = ClientThread(self.SendUploadRequest, Peer_Id, Request,filepath,Filename)
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()
    
    def DOWNLOAD(self, Filename, Peers, currentClient):
        
        FilesServed = FilesServedByClient()

        if Filename in FilesServed:
            print(f"File {Filename} already exists")
            return
        
        print(f"Downloading file {Filename}")
        Request = f"#DOWNLOAD {Filename}"

        SizeOfFile = 0

        # Send the initial #DOWNLOAD request to all peers check if they serve the file
        servingPeersList = []
        for Peer_Id in Peers:
            response = self.SendDownloadRequest(Peer_Id, Request,Filename)
            if response and response.startswith("330"):  # Peer is serving the file
                _, _, _, _, _, _, filesizeInBytes = response.split(" ")
                servingPeersList.append(Peer_Id)
                SizeOfFile = int(filesizeInBytes)


        if not servingPeersList:
            print(f"File {Filename} download failed, peers {', '.join(Peers)} are not serving the file")
            return

        FileDownloadFailed = False 
        chunk_size = 100  # Define the chunk size (in bytes)
        chunk_id = 0
        chunks = {}
        threads = []
        NumberOfChunksInFile = GetNumberOfChunks(SizeOfFile)

        class DownloadFileChunkThread(threading.Thread):
            def __init__(self, client_instance ,peer_id, chunk_id):
                super().__init__()
                self.client_instance = client_instance
                self.peer_id = peer_id
                self.chunk_id = chunk_id

            def run(self):
                nonlocal FileDownloadFailed

                chunkRequest = f"#DOWNLOAD {Filename} chunk {self.chunk_id}"

                try:
                    response = self.client_instance.SendDownloadRequest(self.peer_id, chunkRequest,Filename,False)

                    if response and response.startswith("200"):
                        _, _, _, _, _, chunk_data = response.split(" ", 5)
                        chunks[self.chunk_id] = chunk_data.encode("utf-8")
                except Exception as e:
                    print(f"Error downloading chunk {self.chunk_id} from {self.peer_id}: {e}")

        
        while True:
            peerIndex = chunk_id % len(servingPeersList)

            peerID = servingPeersList[peerIndex]

            thread = DownloadFileChunkThread(self, peerID, chunk_id)
            threads.append(thread)
            thread.start()

            if chunk_id == (NumberOfChunksInFile -1 ):  
                break

            chunk_id += 1
        
        for thread in threads:
            thread.join()

        # Step 6: Check if all chunks are downloaded
        if len(chunks) != chunk_id + 1:
            print(f"File {Filename} download failed")
            return

        #File path for the file to be downloaded
        filepath = os.path.join("served_files", Filename)

        # Step 7: Reconstruct the file from chunks
        with open(filepath, "wb") as f:
            for i in range(len(chunks)):
                f.write(chunks[i])
        print(f"File {Filename} download success")



    def runClient(self):
        while True:
            #Command from user input
            Command = input("Input your command: ")

            #FILELIST COMMAND
            if Command.startswith("#FILELIST"):
                _, *Peers = Command.split()
                self.FILELIST(Peers)
            
            #UPLOAD COMMAND
            elif Command.startswith("#UPLOAD"):
                _, Filename ,*Peers = Command.split()
                self.UPLOAD(Filename, Peers, self.LocalPeerID)

            #DOWNLOAD COMMAND
            elif Command.startswith("#DOWNLOAD"):
                _, Filename ,*Peers = Command.split()
                self.DOWNLOAD(Filename, Peers, self.LocalPeerID)
            
            #INVALID COMMAND
            else:
                print("The command is invalid")
        

if __name__ == "__main__":
    client = ClientMain()
    client.runClient()
