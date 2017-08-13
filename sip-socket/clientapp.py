import argparse
import os
import sys

from xsocket import udpclient
from xsocket import tcpclient

NEW_LINE = '\r\n'

def main():
	parser = argparse.ArgumentParser(description='a configurable socket client (udp/tcp)')

	parser.add_argument('protocol', type=str, choices=['udp', 'tcp'], help='the protocol type')
	parser.add_argument('ip', type=str, help='the ip address of the server')
	parser.add_argument('port', type=int, help='the port number of the server')

	parser.add_argument('-request', type=str, nargs='?', const='Hello, World!', default='Hello, World!', help='the message to be sent to the server periodically')
	parser.add_argument('-period', type=int, nargs='?', const=-1, default=-1, help='the period of message sending/receiving')
	parser.add_argument('-timeout', type=int, nargs='?', const=5, default=5, help='timeout duration for connect/send/receive')
	parser.add_argument('-buffersize', type=int, nargs='?', const=1024, default=1024, help='maximum size of the receiving buffer')
	parser.add_argument('-sslversion', type=str, nargs='?', const=None, default=None, help='ssl/tls version')
	parser.add_argument('-trialcount', type=int, nargs='?', const=10, default=10, help='maximum trial count to connect to server')

	parser.add_argument('--sendloop', dest='sendloop', action='store_true', default=False, help='enable message sending loop')
	parser.add_argument('--recvloop', dest='recvloop', action='store_true', default=False, help='enable message receiving loop')
	parser.add_argument('--sendrecvloop', dest='sendrecvloop', action='store_true', default=False, help='enable message sending/receiving loop')

	args = parser.parse_args()

	if args.protocol == 'udp':
		c = udpclient
	elif args.protocol == 'tcp':
		c = tcpclient
	else:
		sys.exit('unknown protocol: {0}'.format(args.protocol))

	client = c.Client(args.ip, args.port, args.timeout, args.sendloop, args.recvloop, args.sendrecvloop, args.sslversion, args.trialcount)

	client.loop_message = '''INVITE sip:13@10.178.20.130 SIP/2.0
Via: SIP/2.0/TCP 10.178.20.130:20036
From: "Test 15" <sip:15@10.178.20.130>tag=as58f4201b
To: <sip:13@10.178.20.130>
Call-ID: 326371826c80e17e6cf6c29861eb2933@10.178.20.130
Contact: <sip:15@10.178.20.130>
CSeq: 102 INVITE
User-Agent: Asterisk PBX
Max-Forwards: 70
Content-Type: application/sdp
Content-Length: 14

Hello, World!'''

	client.run()

if __name__ == '__main__':
	main()
