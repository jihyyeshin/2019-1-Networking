from socket import *
import os
import sys
import struct
import time
import select
import binascii  

ICMP_ECHO_REQUEST = 8

# checksum 계산 함수
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
    global rttMin, rttMax, rttSum, rttCnt

    timeLeft = timeout # timeout 예외
    while 1:
        startedSelect = time.time() # 현재 
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = (time.time() - startedSelect) # 현재 시간에서 핑을 받는데 까지 걸리는 시간
        if whatReady[0] == []: # Timeout
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        #Fill in start
        #Fetch the ICMP header from the IP packet
        icmpheader=recPacket[20:28]
        type, code, checksum, pid, seq = struct.unpack('bbHHh', icmpheader)

        #OPTION 2
        if type==8 or ID!=pid:#wrong type
        	return 'Wrong Type.'

        send_time,  = struct.unpack('d', recPacket[28:]) # 보낸 시간 패킷에 가서 가져온다. 
        
        #OPTION 1
        rtt = (timeReceived - send_time) * 1000
        rttCnt+=1
        rttSum+=rtt
        rttMin=min(rttMin, rtt)
        rttMax=max(rttMax, rtt)

        ip_header = struct.unpack('!BBHHHBBH4s4s' , recPacket[:20])
        ttl = ip_header[5]
        saddr = inet_ntoa(ip_header[8])
        length = len(recPacket) - 20

        return 'Reply from {}: bytes={} RTT={:.3f}ms TTL={}'.format(saddr, length, rtt, ttl)
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
	myChecksum = checksum(header + data)
	
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

	mySocket = socket(AF_INET, SOCK_RAW, icmp) # 소켓 생성
	
	myID = os.getpid() & 0xFFFF  # Return the current process i, 프로세스 아이디 확인
	sendOnePing(mySocket, destAddr, myID)
	delay = receiveOnePing(mySocket, myID, timeout, destAddr)
	
	mySocket.close()
	return delay
	
def ping(host, timeout=1):
	global rttMin, rttMax, rttSum, rttCnt
	rttMin = float('+inf')
	rttMax = float('-inf')
	rttSum = 0
	rttCnt = 0 # 전역변수 초기화, 이들은 rtt의 결과를 위해 사용된다.
	count = 0 # 손실 개수 측정
	#timeout=1 means: If one second goes by without a reply from the server,
	#the client assumes that either the client's ping or the server's pong is lost
	dest=gethostbyname(host)
	print("Pinging " + dest + " using Python:")
	#Send ping requests to a server separated by approximately one second
	try:
		while 1:
			count += 1
			delay=doOnePing(dest, timeout) # rtt 값을 받음
			print(delay) 
			time.sleep(1) # 1ms 멈춤
	except KeyboardInterrupt:# 종료 버튼
		if count != 0:
			print ("***",host," Ping Result ***")
			print ('{:.1f}% Packet Loss'.format(100.0 - rttCnt * 100.0 / count))
			if rttCnt != 0:
				print ('RTT MIN = {:.3f}ms AVG = {:.3f}ms MAX = {:.3f}ms'.format(rttMin, rttSum / rttCnt, rttMax))

	return delay
ping(sys.argv[1])