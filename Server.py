import socket
import sys
import os
import pickle
import random
import time

def sendMovie( fileName, cHost, cUDPport, sessionID):
	dest = (cHost, cUDPport)
	su = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	# to guarantee that the send buffer has space for the biggest JPEG files
	su.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 32000) 
	frameNo = 1
	fr = open(fileName, 'rb')
	while True:
		dat = fr.read(5) #header

		if len(dat) == 0: 
			return
		else:
			imageLen = int(dat)
			
			playload=fr.read(imageLen)

			if frameNo % 100 == 0:
				print(f'nseq={frameNo} JPEG file size = {len(playload)}')
			header = bytearray(12)

			header[0] = (2<<6) #version2
			
			header[1] = 26 #PT
			
			header[2] = (frameNo >> 8) & 0xFF
			header[3] = frameNo & 0xFF

			timestamp = int(time.time() * 1000) % (2**32)

			header[4:8] = timestamp.to_bytes(4, 'big')
			header[8:12] = sessionID.to_bytes(4, 'big')

			su.sendto( header + playload, dest)
			frameNo = frameNo+1
			time.sleep(0.05)  # one image every 50 ms
			

#ip_addr sock
def handleClient( clientHost, sock):
	# receive fileName and UDP port
	# reply with random sessionID, -1 if file not available

	nreq = sock.recv(128)
	req = pickle.loads(nreq)
	fileName = req[1]
	clientUDPPort = req[0]
	if not os.path.exists(fileName):
		rep=(-1,)
		sock.send(pickle.dumps(rep))
		return
	sid = random.randint(0,4000000)
	rep=(sid,)
	sock.send(pickle.dumps(rep))
	#wait for ack from client
	rep = sock.recv(128)
	if rep.decode() == "Go":
		sock.close()
		sendMovie( fileName, clientHost, clientUDPPort, sid)


if __name__ == "__main__":
    # python Server.py serverTCPPort
	if len(sys.argv)!=2:
		print("Usage: python3 Client.py  ServerTCPControlPort")
		sys.exit(1)
	else:
		serverTCPControlPort = int(sys.argv[1])
		st = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			st.bind(("0.0.0.0", serverTCPControlPort))
		except socket.error as e:
			print(f"Error binding TCP server socket: {e}")
			st.close()
			sys.exit(2)
		st.listen(1)
		while True:
			print("Waiting for client")
			try:
				sa, end = st.accept()
			except KeyboardInterrupt:
				print("server exiting")
				st.close()
				sys.exit(0)
			print(f"Handling client connecting from {end}")
			handleClient( end[0], sa )

