import socket
import hashlib
import requests
import sys
import time
import re
import subprocess
import threading
from _thread import *
from Crypto import Random
from Crypto.PublicKey import RSA
import Crypto.Cipher.AES as AES
from Crypto.Hash import SHA256
import pickle

HOST = ''  # Standard loopback interface address (localhost)
PORT = 13655
tLock = threading.Lock()
def hops(HOST,MAX_TTL):
    TTL = MAX_TTL
    if TTL < 1:
            exit()
    while 1:
        ping = subprocess.Popen(
            ["ping", "-c", "1", "-t", str(TTL), HOST],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )
        ping_out = ping.communicate()
        matcher = re.compile("(\d+) packets transmitted, (\d+) received, \+(\d+) errors, (\d+)% packet loss, time (\d+)ms")
        parsed = matcher.search(str(ping_out))
        if(parsed == None):
            print("tracerouting... "+str(TTL),end='\r')
            TTL = TTL - 1
            continue
        break

    print("tracerouting completed with "+str(TTL+1) +" hops for " + HOST )
    return TTL+1

def rtt(HOST,NUM_OF_PINGS):
                ping = subprocess.Popen(
                        ["ping", "-c", str(NUM_OF_PINGS), HOST],
                        stdout = subprocess.PIPE,
                        stderr = subprocess.PIPE
		)
                ping_out,err = ping.communicate()
                matcher = re.compile("rtt min/avg/max/mdev = (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)")
                parsed = matcher.search(str(ping_out)).groups()
                print("DONE")
                rtt_min = parsed[0]
                rtt_avg = parsed[1]
                rtt_max = parsed[2]
                rtt_std = parsed[3]
                print("ping completed with avg_rtt = "+rtt_avg)
                return rtt_avg
def create_socket():
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	print("Socket Created")
	while 1:
		try:
			s.bind((HOST,PORT))
			break
		except socket.error:
			print("Binding Failed on " + str(PORT) + " ! Please Wait...",end='\r') 
			s.close()
			time.sleep(1)
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	print("Socket has been bounded")
	s.listen(10)
	print("Socket is ready")
	return s

def handshake(s):
        random_generator = Random.new().read
        key = RSA.generate(1024,random_generator)
        #creating public and private keys
        rpublic = key.publickey().exportKey()
        rprivate = key.exportKey()
        pub = s.recv(2048)
        s.send(str('ok').encode())
        signed = pickle.loads(s.recv(2048))
        s.send(str('ok').encode())
        hash = s.recv(2048)
        client_public_key = RSA.importKey(pub)
        #print("TRY TO VERIFY" + str(signed[0]))
        if(client_public_key.verify(hash,signed) is True):
                print("HURRAY - Handshake completed")
                s.send(rpublic)
        return key

def HttpRequest_forward(url):
        r = requests.get(url,allow_redirects=True)
        # typed,ext = str(r.headers.get('content-type')).lower().split('/')
        return r

def safe_communication(conn,priv):
    print("Safe communication established")
    encr_data = conn.recv(2048)
    data = priv.decrypt(encr_data)
    depic = pickle.loads(data)
    dehash = SHA256.new(depic).digest().decode()
    print(dehash)


def clientthread(conn,priv):
        mode = -1
        while 1:
                data = conn.recv(1024)
                #safe_communication(conn,priv)
                end_server,ping_or_url = data.decode().split(",")
                try:
                    remote_ip = socket.gethostbyname(end_server)
                except:
                    print("Hostname could not be resolved")
                    exit()
                matcher = re.compile("^(\d+)$")
                parsed = matcher.search(ping_or_url)
#                print("RECEIVED==============",ping_or_url)
                if(parsed == None):
                    mode = 1
                    req = HttpRequest_forward(ping_or_url)
                    break
                    #file2download
                mode = 0
                parsed = parsed.groups()
                ping_num = parsed[0]
                print(end_server + " benchmark")
                roundtrip = rtt(end_server,ping_num)
                hop_count = hops(end_server,30)
                break
        if(mode is 1):
                print("File request mode...")
                open('down.png','wb').write(req.content)
                conn.send(req.content)
                print("File Sent")
                conn.close()
                return
        print("Relay to end_server rtt is "+ str(roundtrip) + " and "+ str(hop_count) + " hops.")
        conn.send(str(str(roundtrip)+","+str(hop_count)).encode())
        conn.close()

def run():
        s = create_socket()
        while 1:
                conn , addr = s.accept()
                priv = handshake(conn)
                print("Connected with " + addr[0] + " : " + str(addr[1]))
                start_new_thread(clientthread, (conn,priv,))
        s.close()
if __name__ == "__main__":
        run()
v
