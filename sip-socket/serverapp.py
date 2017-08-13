import argparse
import os
import sys

from xsocket import udpserver
from xsocket import tcpserver

def main():
	parser = argparse.ArgumentParser(description='a configurable socket client (udp/tcp)')

	parser.add_argument('protocol', type=str, choices=['udp', 'tcp'], help='the protocol type')
	parser.add_argument('port', type=int, help='the port number of the server')

	parser.add_argument('-buffersize', type=int, nargs='?', const=1024, default=1024, help='maximum size of the receiving buffer')

	parser.add_argument('--sendloop', dest='sendloop', action='store_true', default=False, help='enable message sending loop')
	parser.add_argument('--recvloop', dest='recvloop', action='store_true', default=False, help='enable message receiving loop')

	args = parser.parse_args()

	if args.protocol == 'udp':
		s = udpserver
	elif args.protocol == 'tcp':
		s = tcpserver
	else:
		sys.exit('unknown protocol: {0}'.format(args.protocol))

	server = s.Server(args.port, args.buffersize, args.sendloop, args.recvloop)
	server.run()

if __name__ == '__main__':
	main()
