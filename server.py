import socket
import requests
import sys
import time
import re
import subprocess
import threading
from _thread import *

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

def clientthread(conn):
        while 1:
                data = conn.recv(1024)
                end_server,ping_num = data.decode().split(",")
                try:
                    remote_ip = socket.gethostbyname(end_server)
                except:
                    print("Hostname could not be resolved")
                    exit()
                print(end_server + " benchmark")
                roundtrip = rtt(end_server,ping_num)
                hop_count = hops(end_server,30)
                break
        print("Relay to end_server rtt is "+ str(roundtrip) + " and "+ str(hop_count) + " hops.")
        conn.send(str(str(roundtrip)+","+str(hop_count)).encode())
        conn.close()

def run():
        s = create_socket()
        while 1:
                conn , addr = s.accept()
                print("Connected with " + addr[0] + " : " + str(addr[1]))
                start_new_thread(clientthread, (conn,))
        s.close()
if __name__ == "__main__":
        run()
