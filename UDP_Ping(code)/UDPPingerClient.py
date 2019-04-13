'''
UDP Ping Client 

client에서 목적지 서버에게 10개의 ping메시지를 보낸다.

각 메시지에 대해 client는 대응되는 pong메시지가 반환될 때 RTT(round trip time)를 결정 & 출력

클라이언트 또는 서버가 보낸 패킷이 손실될 수 있다.

클라이언트가 서버로 부터의 응답을 1초까지 기다리도록 하고, 응답이 오지 않으면 손실을 가정하고 메시지를 출력
'''
import time
import socket
from socket import *

minRtt=100
maxRtt=0
avgRtt=0
pLossRate=0

# 10개의 ping 메시지를 보낸다.
for i in range(1, 11):

	# 클라이언트 소캣 생성
	clientSocket = socket(AF_INET, SOCK_DGRAM)

	# 1초 기다림, 1초 이내에 회신을 받지 못한 경우 - 손실을 가정
	clientSocket.settimeout(1)

	# 주소, port번호 설정
	addr=("127.0.0.1", 8000)

	start = time.time()

	# hello 문자열을 인코딩해서 서버에 보냄
	clientSocket.sendto("ping".encode(), addr)

	# server로 부터 도착한 data를 출력
	try:
	   	data, server = clientSocket.recvfrom(1024)
	   	end = time.time()
	   	elapsed=float(format(end-start,".6f"))
	   	print ("{0} {1} {2}".format(data, i, elapsed)+"\n")

	   	# rtt 계산
	   	if elapsed > maxRtt:
	   		maxRtt=elapsed
	   	if elapsed < minRtt:
	   		minRtt=elapsed
	   	avgRtt+=elapsed

	# 요청 시간 초과
	except timeout:
		print (str(i)+": REQUESTED TIMED OUT\n")
		pLossRate+=1

# optional exercises
print ("RTT : min = "+str(minRtt)+" max = "+str(maxRtt)+" avg ="+format(avgRtt/10, ".6f"))
print ("Packet Loss Rate : "+str(pLossRate/10*100)+" %")
clientSocket.close()