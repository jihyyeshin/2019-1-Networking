from socket import *
import os
import sys
import struct
import time
import select
import binascii  

ICMP_ECHO_REQUEST = 8

#checksum 계산 함수
def checksum(string): 
	csum = 0
	countTo = (len(string) // 2) * 2  
	count = 0

	while count < countTo:
		thisVal = string[count+1] * 256 + string[count]
		csum = csum + thisVal 
		csum = csum & 0xffffffff  
		count = count + 2
	
	if countTo < len(string):
		csum = csum + string[len(string) - 1]
		csum = csum & 0xffffffff 
	
	csum = (csum >> 16) + (csum & 0xffff)
	csum = csum + (csum >> 16)
	answer = ~csum 
	answer = answer & 0xffff 
	answer = answer >> 8 | (answer << 8 & 0xff00)
	return answer

# ping 받기, socket, id, timeout, destaddr
def receiveOnePing(mySocket, ID, timeout, destAddr):
    #global rtt_min, rtt_max, rtt_sum, rtt_cnt
    timeLeft = timeout# timeout 예외
    while 1:
        startedSelect = time.time()#현재 
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect)# 현재 시간에서 핑을 받는데 까지 걸리는 시간
        if whatReady[0] == []: # Timeout
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        #Fill in start
        #Fetch the ICMP header from the IP packet
        icmpheader=recPacket[20:28]
        type, code, checksum, pid, seq = struct.unpack('bbHHh', icmpheader)

        # if type != 0:
        #     return 'expected type=0, but got {}'.format(type)
        # if code != 0:
        #     return 'expected code=0, but got {}'.format(code)
        # if ID != pid:
        #     return 'expected pid={}, but got {}'.format(ID, pid)
        send_time,  = struct.unpack('d', recPacket[28:])# 보낸 시간 패킷에 가서 가져온다. 
        
        rtt = (timeReceived - send_time) * 1000
        # rtt_cnt += 1
        # rtt_sum += rtt
        # rtt_min = min(rtt_min, rtt)
        # rtt_max = max(rtt_max, rtt)

        ip_header = struct.unpack('!BBHHHBBH4s4s' , recPacket[:20])
        ttl = ip_header[5]
        saddr = inet_ntoa(ip_header[8])
        length = len(recPacket) - 20

        return 'Reply from {}: bytes={} time={:.3f}ms TTL={}'.format(saddr, length, rtt, ttl)
        #Fill in end

        timeLeft = timeLeft - howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."

def sendOnePing(mySocket, destAddr, ID):
	# Header is type (8), code (8), checksum (16), id (16), sequence (16)
	
	myChecksum = 0
	# Make a dummy header with a 0 checksum
	# struct -- Interpret strings as packed binary data
	header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
	data = struct.pack("d", time.time())
	# Calculate the checksum on the data and the dummy header.
	myChecksum = checksum((header + data))
	
	# Get the right checksum, and put in the header
	if sys.platform == 'darwin':
		# Convert 16-bit integers from host to network  byte order
		myChecksum = htons(myChecksum) & 0xffff		
	else:
		myChecksum = htons(myChecksum)
		
	header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
	packet = header + data
	
	mySocket.sendto(packet, (destAddr, 1)) # AF_INET address must be tuple, not str
	# Both LISTS and TUPLES consist of a number of objects
	# which can be referenced by their position number within the object.


def doOnePing(destAddr, timeout): 
	icmp = getprotobyname("icmp")
	# SOCK_RAW is a powerful socket type. For more details:   http://sock-raw.org/papers/sock_raw

	mySocket = socket(AF_INET, SOCK_RAW, icmp)
	
	myID = os.getpid() & 0xFFFF  # Return the current process i
	sendOnePing(mySocket, destAddr, myID)
	delay = receiveOnePing(mySocket, myID, timeout, destAddr)
	
	mySocket.close()
	return delay
	
def ping(host, timeout=1):
    #global rtt_min, rtt_max, rtt_sum, rtt_cnt
    rtt_min = 1
    rtt_max = 0
    rtt_sum = 0
    rtt_cnt = 0
    cnt = 0
    #timeout=1 means: If one second goes by without a reply from the server,
    #the client assumes that either the client's ping or the server's pong is lost
    dest = gethostbyname(host)
    print ("Pinging " + dest + " using Python:")
    #Send ping requests to a server separated by approximately one second
    try:
        while True:
            cnt += 1
            print (doOnePing(dest, timeout))
            time.sleep(1)
    except KeyboardInterrupt:
        if cnt != 0:
            print ('--- {} ping statistics ---'.format(host))
            print ('{} packets transmitted, {} packets received, {:.1f}% packet loss'.format(cnt, rtt_cnt, 100.0 - rtt_cnt * 100.0 / cnt))
            if rtt_cnt != 0:
                print ('round-trip min/avg/max {:.3f}/{:.3f}/{:.3f} ms'.format(rtt_min, rtt_sum / rtt_cnt, rtt_max))

ping(sys.argv[1])