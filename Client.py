from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket
import threading, sys, traceback, os
import sys
import time
import pickle
import select

class Client:
    def __init__(self, master, sId, pUDP, sTCP):
        self.master = master
        self.createWidgets()
        self.frameNo=1
        self.socketUDP = self.createUDPSocket(pUDP)
        self.socketTCP = sTCP
        self.sessionId = sId
        self.imageFile = 'temp.jpeg'


    def createUDPSocket(self, portUDP):
        try:
            s = socket.socket( socket.AF_INET, socket.SOCK_DGRAM)
            s.bind( ("0.0.0.0", portUDP))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 32000)
            
        except socket.error as e:
            print(f"Error binding socket: {e}")
            sys.exit(2)
        return s
        
    def createWidgets(self):
        """Build GUI."""
        # Create Play button		
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=1, column=1, padx=2, pady=2)
        
        # Create End button		
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "End"
        self.start["command"] = self.closeWindow
        self.start.grid(row=1, column=2, padx=2, pady=2)
        # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5)
        
    def playMovie(self):
        threading.Thread(target=self.playJPEGs).start()
        self.socketTCP.send("Go".encode())
        self.socketTCP.close() 
        
    def playJPEGs(self):
        while True:
            infds, outfds, errfds = select.select([self.socketUDP],[],[], 2)
            #print(f'infds={infds}')
            if infds==[]:
                break
            dat, r = self.socketUDP.recvfrom( 16384 )
            version = (dat[0] >> 6) & 0x03
            pt = dat[1] & 0x7F
            sequence = int.from_bytes(dat[2:4], 'big')
            timestamp = int.from_bytes(dat[4:8], 'big')
            ssrc = int.from_bytes(dat[8:12], 'big')


            if version == 2 and pt == 26 and ssrc == self.sessionId:
                if sequence > self.frameNo:
                    self.frameNo = sequence

                    #print(f'len={len(dat)}')
                    fw = open('temp.jpeg', 'wb')
                    fw.write(dat[12:])
                    fw.close()
                    img = Image.open(self.imageFile)
                    w = img.width
                    l = img.height
                    #print(f'w={w}. l={l}')
                    photo = ImageTk.PhotoImage(img)
                    self.label.configure(image = photo,height=l)
                    self.label.image = photo
                    #self.frameNo = self.frameNo+1
            
    def closeWindow(self):
        print("Destroying window")
        self.master.destroy() # Close the gui window
        os.remove(self.imageFile)

            
def contactServer( serverName, serverTCPControlPort, ClientUDPport, fileName):
    s = socket.socket( socket.AF_INET, socket.SOCK_STREAM )
    # connect to server control port and send message with file name and clientUDPport
    # receive a sessionID; only used for checking
    try:
        s.connect((serverName, serverTCPControlPort))
    except socket.error as e:
        print(f"Error connect TCP server socket: {e}")
        s.close()
        sys.exit(3)
    msg = ( ClientUDPport, fileName )
    nmsg = pickle.dumps(msg)
    s.send(nmsg)
    nrep = s.recv(128)
    rep = pickle.loads(nrep)
    print(f'SessionId = {rep[0]}')
    return rep[0], s

if __name__ == "__main__":
    # python3 Client.py ServerName ServerTCPControlPort ClientUDPport fileName
    if len(sys.argv)!=5:
        print("Usage: python3 Client.py ServerName ServerTCPControlPort ClientUDPport fileName")
        sys.exit(1)
    else:
        serverName = sys.argv[1]
        serverTCPControlPort = int(sys.argv[2])
        clientUDPport = int(sys.argv[3])
        fileName = sys.argv[4]
        # contact server, obtaining a session ID. -1 if file does not exist
        sessionId, sockTCP = contactServer( serverName, serverTCPControlPort, clientUDPport, fileName)
        if sessionId < 0:
            print("Server refused to send video!")
            sys.exit(2)
        else:
            print("Creating window to play video")
            root = Tk()
            # Create a new client
            app = Client(root, sessionId, clientUDPport, sockTCP)
            app.master.title("Player")
            root.mainloop()
