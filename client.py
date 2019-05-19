#!/usr/bin/env python3

import hashlib
import socket
import requests
import argparse
import time
import sys
import os
import re
import subprocess
import threading
import Crypto
from Crypto import Random
from Crypto.PublicKey import RSA
import Crypto.Cipher.AES as AES
from Crypto.Hash import SHA256
from Crypto.PublicKey import DSA

import pickle

threads = []
statistics = []
tLock = threading.Lock()

#Function will return the index of the route in statistics
def RouteSelection(factor):
        print("Route Selection was initiated")
        statistics_tmp = []
        statistics_equal = []
        Count = 0
        if factor == 'latency':
                for s in statistics:
                        print(s.rtt)
                        statistics_tmp.append(s.rtt)
                Min = min(statistics_tmp)
                print('Min rtt is: ' + str(Min))

                for s in statistics:
                        for s1 in statistics:
                                if s1.rtt == s.rtt:
                                        Count += 1

                if Count > len(statistics):
                        print("Two or more routs have the same RTT value. Hops factor will be applied")

#If there are >=2 equal we chance factor
                        Count = 0
                        for s in statistics:
                                print(s.hops)
                                statistics_equal.append(int(s.hops))
                        Min = min(statistics_equal)
                        print('Min hops are: ' + str(Min))

                        for s in statistics:
                                if Min == s.hops:
                                        Count += 1
                        print('Min hops appears: ' + str(Count) + ' times')
                        if Count > 1:
                                index = 0
                                for s2 in statistics:
                                        if s2.hops  == Min :
                                                break
                                        index += 1
                                print(index)
                                return index
                        #ELSE
                        index = 0
                        for s2 in statistics:
                                if s2.hops == Min :
                                        break
                                index +=1
                        print(index)
                        return index

#Find the index of the Min
                index = 0
                for s2 in statistics:
                        if(s2.rtt == Min):
                                break
                        index += 1
                print(index)
                return index


        if factor == 'hops':
                for s in statistics:
                        print(s.hops)
                        statistics_tmp.append(int(s.hops))
                Min = min(statistics_tmp)
                print('Min hops are: ' + str(Min))

                for s in statistics:
                        for s1 in statistics:
                                if s1.hops == s.hops:
                                        Count += 1
#if there are >=2 equal. We chance factor
                if Count > len(statistics):
                        print(bcolors.WARNING+"Two or more routes have the same Hops. RTT factor will be applied..."+bcolors.ENDC)
                        Count = 0
                        for s in statistics:
                                print(s.rtt)
                                statistics_equal.append(s.rtt)
                        Min = min(statistics_equal)
                        print("Min RTT: " + str(Min))

                        for s in statistics:
                                if Min == s.rtt:
                                        Count += 1
                        print("Min RTT appears: " + str(Count) + " times")
                        if Count > 1:
                                print("The number of results is greater that 1. Route will be random")
                                index = 0
                                for s2 in statistics:
                                        if(s2.rtt == Min):
                                                break
                                        index += 1
                                print(index)
                                return index
                        #ELSE
                        index = 0
                        for s2 in statistics:
                                if (s2.rtt == Min):
                                        break
                                index += 1
                        print(index)
                        return index

        #if hops was enough
                index = 0
                for s2 in statistics:
                        if(s2.hops == Min):
                                break
                        index += 1
                print(index)
                return index

def acquire_relays_from_file():
    relays = []
    f1 = open(args.rels,"r")
    for line in f1:
        x,y,z = line.split(", ")
        relays.append((y,int(z)))
    return relays




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
    def __init__(self,relay_host,rtt,hops,port):
        self.relay_host = relay_host
        self.port = port
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
            key = RSA.generate(1024)
            #creating public and private keys
            public = key.publickey().exportKey()
            text = b"36553653"
            hash = SHA256.new(text).digest()
            signature = key.sign(hash, '')
            print('signature=', signature)
            s.send(public)
            s.recv(1024)
            s.send(pickle.dumps(signature))
            s.recv(1024)
            s.send(hash)
            rpub = s.recv(1024)
            msg = str('geia').encode()
            #crypto
            #hash = SHA256.new(msg).digest()
            #signature = key.sign(hash,'')
            #hash = pickle.dumps( str(hash) +'|'+ str(signature[0]))
            #rkey = RSA.importKey(rpub)
            #rkey.encrypt(hash,4096)
            #s.send(hash)

            return s,public,key,rpub

    except  socket.error:
            print("Failed to Connect")
            sys.exit()

def benchmark(RELAY_HOST,RELAY_PORT,end_server,num_of_pings):
    s,pub,key,rpub = create_socket_with_host(RELAY_HOST,RELAY_PORT)
    s.send(str(end_server+','+num_of_pings).encode())
    data = s.recv(1024)#have to send to relay num of pings
    matcher = re.compile("(\d+.\d+),(\d+)")
    parsed = matcher.search(str(data)).groups()
    print(bcolors.OKGREEN+'Relay '+threading.currentThread().host +' sent '+ parsed[0]+' rtt and '+ parsed[1]+' hops from relay->end_server' + bcolors.ENDC)
    client_relay_rtt = rtt(RELAY_HOST,str(num_of_pings))
    client_relay_hops = hops(RELAY_HOST,30)
    print(bcolors.OKGREEN+'Client -> Relay '+threading.currentThread().host +' sent '+ str(client_relay_rtt)+' rtt and '+ str(client_relay_hops)+' hops' + bcolors.ENDC)
    tLock.acquire()
    new_benchmark = Relay_benchmark(RELAY_HOST,str(round(float(parsed[0]) + float(client_relay_rtt),3)),str(int(parsed[1]) + int(client_relay_hops)),RELAY_PORT)
    statistics.append(new_benchmark)
    tLock.release()
    s.close()

def HttpRequest(HOST,PORT,END):
    url = input("Type the file's url to download from the end-server: ")
    if(END is HOST):#direct
        r = requests.get(url,allow_redirects=True)
        typed,ext = str(r.headers.get('content-type')).lower().split('/')
        open('downloaded.'+ext, 'wb').write(r.content)
    else:
        s,pub,key,rpub = create_socket_with_host(HOST,PORT)
        s.send(str(END+','+url).encode())
        print("Request Sent",END,url)
        start = time.time()
        while True:
                data = s.recv(1024)#have to send to relay num of ping
                # typed,ext = str(data.headers.get('content-type')).lower().split('/')
                if not data:
                        break
                open('downloaded.png', 'ab+').write(data)
        end = time.time()
        print(bcolors.OKBLUE+'Download time for file ',str(round(end-start,3))+bcolors.ENDC)

def main_thread(end_server,ping_num):
    print("Initiated")

# file IO
# have to pass in the latency for beanchmarking purposes
    relays = acquire_relays_from_file()
    i = 0
    for r in relays:
        threadX = myThread(i,r[0],r[1],end_server,ping_num)
        threads.append(threadX)
        i +=1


    for t in threads:
        t.start()

    for t in threads:
        t.join()

    for s in statistics:
        print(bcolors.OKBLUE +'Route through '+ s.relay_host,s.rtt , s.hops,bcolors.ENDC)
    direct = Relay_benchmark(end_server,str(rtt(end_server,str(ping_num))),str(hops(end_server,30)),80)
    statistics.append(direct)
    print(bcolors.OKBLUE+"Direct hops " + direct.hops + " and with avg rtt "+direct.rtt+bcolors.ENDC)


if __name__ == "__main__": 
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--ends')
    parser.add_argument('-r', '--rels')
    args = parser.parse_args()

    f1 = open(args.ends,"r")
    print(f1.read())
    f1.close()

#getting the infos from command line
    End_server_alias , Number_of_pings , Selection_factor = (input("Type informations of the end-server you want to connect with: ") or "google 1 latency").split()

#Search for the alias in file
    End_server = SearchAlias(End_server_alias)
    print(End_server)
    main_thread(End_server,Number_of_pings) #define run as main func
    best_route_index = RouteSelection(Selection_factor)
    best_route = statistics[best_route_index]
    route_path = best_route.relay_host
    if(best_route.relay_host==End_server):
        route_path = "direct to "+End_server
    print(bcolors.OKBLUE + "Selecting optimal route : (" +route_path,best_route.rtt,best_route.hops+")"+bcolors.ENDC)
    HttpRequest(best_route.relay_host,best_route.port,End_server) 
    print("Exiting main thread")
