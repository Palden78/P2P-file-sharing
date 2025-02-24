import os
import socket


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


#Function to send request to a peer
def SendRequest(Peer_Id, Request):

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
        print(f"Error connecting to {Peer_Id}: {ex}")
    finally:
        #close the socket
        sock.close()

def FILELIST(Peers):
    #Request to be sent
    Request = "#FILELIST"
    for Peer_Id in Peers:
        #Send the request to the respective peer
        SendRequest(Peer_Id, Request)


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

def UPLOAD(Filename, Peers, currentClient):
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
    print(f"Uploading file {Filename}")
    Request = f"#UPLOAD {Filename} bytes {SizeOfFile}"

    for Peer_Id in Peers:
        #Send the request to the respective peer
        response = SendRequest(Peer_Id, Request)

        if response.startswith("330"):

            with open(filepath, "rb") as f:
                chunk_id = 0
                while chunk := f.read(100):
                    chunkRequest = f"#UPLOAD {Filename} chunk {chunk_id} {chunk.decode('utf-8')}"
                    SendRequest(Peer_Id, chunkRequest)
                    chunk_id +=1

            completion_response = SendRequest(Peer_Id, "UPLOAD_COMPLETE")
            
            if completion_response and "200 File" in completion_response:
                print(f"File {Filename} upload success to {Peer_Id}")
            else:
                print(f"File {Filename} upload failed to {Peer_Id}")





    

if __name__ == "__main__":
    # Get the name of the current client launching client.py 
    current_client = os.path.basename(os.getcwd())
    
    #Continuously get command from the client
    while True:
        #Command from user input
        Command = input("Input your command: ")

        #FILELIST COMMAND
        if Command.startswith("#FILELIST"):
            _, *Peers = Command.split()
            FILELIST(Peers)
        
        #UPLOAD COMMAND
        elif Command.startswith("#UPLOAD"):
            _, Filename ,*Peers = Command.split()
            UPLOAD(Filename, Peers, current_client)

        #DOWNLOAD COMMAND
        elif Command.startswith("#DOWNLOAD"):
            _, *Peers = Command.split()
            DOWNLOAD(Peers)
        
        #INVALID COMMAND
        else:
            print("The command is invalid")
