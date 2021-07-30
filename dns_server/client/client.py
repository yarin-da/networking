import sys
import socket

server_ip = sys.argv[1]
server_port = int(sys.argv[2])
# init UDP socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

while True:
    user_input = input('Enter a domain: ')
	# send user request (i.e. a domain)
    s.sendto(bytes(user_input, 'utf-8'), (server_ip, server_port))
	# receive server's answer
    data, addr = s.recvfrom(1024)

	# get rid of non-relevant information (i.e. extract only the IP address)
    ip = data.decode('utf-8').split(',')[1] 

    print(ip)
    
