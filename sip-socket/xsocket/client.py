"""provides the common interface of client classes

Classes:
    Client: base class for UDP/TCP clients
"""


import socket
import ssl
import sys
import threading
import time

class Client(object):
    """Base Class for UDP/TCP Client

    Constants:
        UDP: socket constants for UDP
        TCP: socket constants for TCP
        SSL_VERSION_MAP: ssl version string map

    Attributes:
        protocol: protocol (UDP/TCP)
        ip_address: server ip address
        port: server port
        timeout: timeout for connect/send/recv
        address: server address object
        socket: underlying socket object (possibly with TLS)
        root_socket: underlying socket object
        sslversion: SSL/TLS version
        maximum_trial_count: connect attemp limit
        loop_message: message to send periodically
        loop_buffersize: recv buffer size to recv periodically
        loop_period_send: period of send loop
        loop_period_recv: period of recv loop
        loop_period_sendrecv: period of sendrecv loop
        enable_send_loop: enable send loop
        enable_recv_loop: enable recv loop
        enable_sendrecv_loop: enable sendrecv loop
        send_thread: send_thread
        recv_thread: recv_thread
        sendrecv_thread: sendrecv_thread
        trial_count: trial_count

    Methods:
        connect: connect to server
        send: send message to server
        send_loop: send periodically
        recv: recv from server
        recv_loop: recv periodically
        sendrecv: send to and then recv from server
        sendrecv_loop: sendrecv periodically
        disconnect: disconnect from server
        run: run the client as configured

    Child Interface Methods:
        connectx: connect callback
        sendx: send callback
        recvx: recv callback

    Internal Methods:
        connectssl: perform ssl wrapping
    """

    UDP = socket.SOCK_DGRAM
    TCP = socket.SOCK_STREAM

    SSL_VERSION_MAP = {
        #"tls"      : ssl.PROTOCOL_TLS,
        #"tlsclient": ssl.PROTOCOL_TLS_CLIENT,
        #"tlsserver": ssl.PROTOCOL_TLS_SERVER,
        "ssv23"    : ssl.PROTOCOL_SSLv23,
        #"ssv2"     : ssl.PROTOCOL_SSLv2,
        #"ssv3"     : ssl.PROTOCOL_SSLv3,
        "tlsv1"    : ssl.PROTOCOL_TLSv1,
        "tlsv11"   : ssl.PROTOCOL_TLSv1_1,
        "tlsv12"   : ssl.PROTOCOL_TLSv1_2,
    }

    def __init__(
            self, protocol, ip_address, port, timeout,
            sendloop, recvloop, sendrecvloop,
            sslversion, maximum_trial_count):
        print('client configuring...')

        self.protocol = protocol
        self.ip_address = ip_address
        self.port = port
        self.timeout = timeout
        self.address = (self.ip_address, self.port)
        self.socket = socket.socket(socket.AF_INET, self.protocol)
        self.root_socket = self.socket
        self.sslversion = sslversion
        self.maximum_trial_count = maximum_trial_count

        self.loop_message = ''

        self.loop_buffersize = 1024
        self.loop_period_send = 10
        self.loop_period_recv = 2
        self.loop_period_sendrecv = 5

        self.enable_send_loop = sendloop
        self.enable_recv_loop = recvloop
        self.enable_sendrecv_loop = sendrecvloop

        self.send_thread = threading.Thread(target=self.send_loop)
        self.recv_thread = threading.Thread(target=self.recv_loop)
        self.sendrecv_thread = threading.Thread(target=self.sendrecv_loop)

        self.trial_count = 0

    def connectx(self):
        """abstract connect method expected to be implemented by child class
        """

        raise Exception('Client::connectx method must be implemented by child class')

    def connectssl(self, sslversion):
        """wrap socket by ssl context with the given sslversion
        """

        ssl_version = self.SSL_VERSION_MAP.get(sslversion)

        if ssl_version is None:
            raise Exception('invalid ssl version: {}'.format(sslversion))

        self.socket = ssl.wrap_socket(
            self.root_socket,
            ssl_version=ssl_version,
            do_handshake_on_connect=False,
            suppress_ragged_eofs=False,
            ciphers='AES128-SHA256')

        try:
            self.socket.do_handshake()
        except ssl.SSLEOFError as error:
            print('ssl handshake error')
            sys.exit(error)
        except socket.error as error:
            print('socket error')
            sys.exit(error)

    def connect(self):
        """connect to the socket
        """

        print('client connecting...')

        if self.sslversion is None:
            self.socket.settimeout(self.timeout)

        try:
            self.connectx()
        except socket.error as error:
            print('unable to connect:\n{error}'.format(error=error))
            self.trial_count += 1

            if self.trial_count < self.maximum_trial_count:
                print('attemp {count}/{maximum} to connect...'.format(
                    count=self.trial_count,
                    maximum=self.maximum_trial_count))
                self.connect()
            else:
                raise Exception('maximum trial count reached\n{0}'.format(error))

        if self.sslversion == 'all':
            connected = False
            error = None
            for sslversion in self.SSL_VERSION_MAP:
                try:
                    self.connectssl(sslversion)
                    connected = True
                    break
                except Exception as error:
                    pass
            if not connected:
                raise error
        elif self.sslversion is not None:
            self.connectssl(self.sslversion)

        print('client connected')

    def sendx(self, message):
        """abstract send method expected to be implemented by child class
        """

        raise Exception('Client::sendx method must be implemented by child class')

    def send(self, message):
        """send the given message to the server
        """

        self.sendx(message)
        print('send ({length})'.format(length=len(message)))
        print(message.splitlines()[0])

    def send_loop(self):
        """send the loop message to the server periodically
        """

        while True:
            try:
                self.send(self.loop_message)
            except Exception as error:
                print('send_loop error: {error}'.format(error=error))
                break
            time.sleep(self.loop_period_send)

    def recvx(self, buffersize):
        """abstract recv method expected to be implemented by child class
        """

        raise Exception('Client::recvx method must be implemented by child class')

    def recv(self, buffersize):
        """recv from the server setting the given buffersize
        """

        message = self.recvx(buffersize)
        print('recv ({length})'.format(length=len(message)))
        print(message.splitlines()[0])

        return message

    def recv_loop(self):
        """recv from the server periodically
        """

        while True:
            try:
                self.recv(self.loop_buffersize)
            except Exception as error:
                print('recv_loop error: {error}'.format(error=error))
                break
            time.sleep(self.loop_period_recv)

    def sendrecv(self):
        """first send to and then recv from the server
        """

        self.send(self.loop_message)
        self.recv(self.loop_buffersize)

    def sendrecv_loop(self):
        """send to and then recv from the server periodically
        """

        while True:
            try:
                self.sendrecv()
            except Exception as error:
                print('sendrecv_loop error: {error}'.format(error=error))
                break
            time.sleep(self.loop_period_sendrecv)

    def disconnect(self):
        """disconnect from server
        """

        print('client disconnecting...')
        self.socket.close()

    def run(self):
        """connect to the server
        start all desired threads
        when completed disconnect from the server
        """

        self.connect()
        if self.enable_send_loop:
            self.send_thread.start()
        if self.enable_recv_loop:
            self.recv_thread.start()
        if self.enable_sendrecv_loop:
            self.sendrecv_thread.start()
        if self.enable_send_loop:
            self.send_thread.join()
        if self.enable_recv_loop:
            self.recv_thread.join()
        if self.enable_sendrecv_loop:
            self.sendrecv_thread.join()
        self.disconnect()
