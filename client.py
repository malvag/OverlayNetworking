#!/usr/bin/env python3

import socket
import requests
import argparse
import time
import sys
import os
import re
import subprocess
import threading

threads = []
statistics = []
tLock = threading.Lock()

def SearchAlias(Alias):
	f1 = open(args.ends,"r")
	for line in f1:
		x,y = line.split(", ")
		Alias_y = y[:(len(y)-1)]
		print(x,y,Alias,Alias_y)
		if Alias_y == Alias or y == Alias:
			return x
	print("False alias as input \n")
	f1.close()

class myThread (threading.Thread):
    def __init__(self, threadID, host,port,end_server,ping_num):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = "Thread"+str(threadID)
        self.host = host
        self.port = port
        self.end_server = end_server
        self.ping_num = ping_num
    def run(self):
        print ("Starting " + self.name)
        if(self.host is None):
            sys.exit()
        benchmark(self.host,self.port,self.end_server,self.ping_num)
        print ("Exiting " + self.name)

class Relay_benchmark:
    def __init__(self,relay_host,rtt,hops):
        self.relay_host = relay_host
        self.rtt = rtt
        self.hops = hops

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def rtt(HOST,NUM_OF_PINGS):
    ping = subprocess.Popen(
        ["ping", "-c", NUM_OF_PINGS, HOST],
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE
    )

    ping_out,err = ping.communicate()
    matcher = re.compile("rtt min/avg/max/mdev = (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)")
    parsed = matcher.search(str(ping_out)).groups()
    rtt_min = parsed[0]
    rtt_avg = parsed[1]
    rtt_max = parsed[2]
    rtt_std = parsed[3]
    print("ping completed with avg_rtt = "+rtt_avg)
    return rtt_avg

def hops(HOST,MAX_TTL):
    TTL = MAX_TTL
    while 1:
        ping = subprocess.Popen(
            ["ping", "-c", "1", "-t", str(TTL), HOST],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE
        )
        ping_out = ping.communicate()
        matcher = re.compile("(\d+) packets transmitted, (\d+) received, \+(\d+) errors, (\d+)% packet loss, time (\d+)ms")
        parsed = matcher.search(str(ping_out))
        # print(TTL)
        if(parsed == None and TTL >0):
            print("tracerouting... "+str(TTL),end='\r') 
            TTL = TTL - 1
            continue
        print("tracerouting completed",end='\r') 
        break

    print(str(TTL+1) +" hops for " + HOST )
    return TTL+1

def create_socket_with_host(HOST,PORT):
    print("Socket Created")

    try:
            remote_ip = socket.gethostbyname(HOST)
    except  socket.gaierror:
            print("HostName could not be resolved")
            sys.exit()

    print("IP Address "+ remote_ip)
    try:
            s= socket.socket(socket.AF_INET,socket.SOCK_STREAM)

            s.connect((remote_ip,PORT))
            
            print("Socket connected to "+ HOST + " on "+ remote_ip )
            return s

    except  socket.error:
            print("Failed to Connect")
            sys.exit()

def benchmark(RELAY_HOST,RELAY_PORT,end_server,num_of_pings):
    s = create_socket_with_host(RELAY_HOST,RELAY_PORT)
    s.send(str(end_server+','+num_of_pings).encode())
    data = s.recv(1024)#have to send to relay num of pings
    matcher = re.compile("(\d+.\d+),(\d+)")
    parsed = matcher.search(str(data)).groups()
    print(bcolors.OKGREEN+'Relay '+threading.currentThread().host +' sent '+ parsed[0]+' rtt and '+ parsed[1]+' hops from relay->end_server' + bcolors.ENDC)
    client_relay_rtt = rtt(RELAY_HOST,str(num_of_pings))
    client_relay_hops = hops(RELAY_HOST,30)
    print(bcolors.OKGREEN+'Client -> Relay '+threading.currentThread().host +' sent '+ str(client_relay_rtt)+' rtt and '+ str(client_relay_hops)+' hops' + bcolors.ENDC)
    tLock.acquire()
    new_benchmark = Relay_benchmark(RELAY_HOST,str(round(float(parsed[0]) + float(client_relay_rtt),3)),str(int(parsed[1]) + int(client_relay_hops)))
    statistics.append(new_benchmark)
    tLock.release()
    s.close()


def main_thread(end_server,ping_num):
    print("Initiated")

# file IO
# have to pass in the latency for beanchmarking purposes
    thread1 = myThread(0,'kos.csd.uoc.gr',13655,end_server,ping_num)
    thread2 = myThread(1,'dia.csd.uoc.gr',13655,end_server,ping_num)
    thread3 = myThread(2,'naxos.csd.uoc.gr',13655,end_server,ping_num)
    thread4 = myThread(3,'limnos.csd.uoc.gr',13655,end_server,ping_num)

    threads.append(thread1)
    threads.append(thread2)
    threads.append(thread3)
    threads.append(thread4)


    for t in threads:
        t.start()

    for t in threads:
        t.join()

    for s in statistics:
        print(bcolors.OKBLUE +'Route through '+ s.relay_host,s.rtt , s.hops,bcolors.ENDC)
    print(bcolors.OKBLUE+"Direct hops " + str(hops(end_server,30)) + " and with avg rtt "+str(rtt(end_server,"2"))+bcolors.ENDC)
    print ("Exiting Main Thread")

    


if __name__ == "__main__": 
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--ends')
    parser.add_argument('-r', '--rels')
    args = parser.parse_args()

    f1 = open(args.ends,"r")
    print(f1.read())
    f1.close()

#getting the infos from command line
    End_server_alias , Number_of_pings , latency = input("Type informations of the end-server you want to connect with: ").split()

#Search for the alias in file
    End_server = SearchAlias(End_server_alias)
    print(End_server)
    main_thread(End_server,Number_of_pings) #define run as main func