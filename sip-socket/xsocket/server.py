import datetime
import socket
import ssl
import threading

import notifier

class Server(notifier.Notifier):

    UDP = socket.SOCK_DGRAM
    TCP = socket.SOCK_STREAM

    WILL_START = 'will_start'
    DID_START  = 'did_start'

    WILL_ACCEPT = 'will_accept'
    DID_ACCEPT  = 'did_accept'

    WILL_STOP = 'will_stop'
    DID_STOP  = 'did_stop'

    WILL_SHUTDOWN = 'will_shutdown'
    DID_SHUTDOWN  = 'did_shutdown'

    WILL_RUN = 'will_run'
    DID_RUN  = 'did_run'

    def __init__(self, protocol, port, buffersize, sendloop, recvloop):
        notifier.Notifier.__init__(self)

        print('server configuring...')

        self.protocol    = protocol
        self.port        = port
        self.buffersize  = buffersize
        self.sendloop    = sendloop
        self.recvloop    = recvloop
        self.socket      = socket.socket(socket.AF_INET, self.protocol)
        self.root_socket = self.socket
        self.loop_thread = threading.Thread(target=self.loop)
        self.sessions    = {}

    def startx(self):
        raise Exception('Server::startx method must be implemented by child class')

    def start(self):
        self.notify_all(self.WILL_START)
        print('server starting...')
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(('', self.port))
        self.startx()
        self.notify_all(self.DID_START)

    def acceptx(self):
        raise Exception('Server::acceptx method must be implemented by child class')

    def accept(self):
        self.notify_all(self.WILL_ACCEPT)
        print('waiting for client...')
        session = self.acceptx()
        if session.address not in self.sessions:
            session.enable_send_loop = self.sendloop
            session.enable_recv_loop = self.recvloop
            session.register(self)
            session.start()
            self.sessions[session.address] = session
            print('client registered: {address}'.format(address=session.address))
            self.notify_all(self.DID_ACCEPT, session)

    def loop(self):
        while True:
            self.accept()

    def stop(self):
        self.notify_all(self.WILL_STOP)
        print('server stopping...')
        self.socket.close()
        self.notify_all(self.DID_STOP)

    def shutdown(self):
        self.notify_all(self.WILL_SHUTDOWN)
        print('server shutting down...')
        self.socket.shutdown(socket.SHUT_WR)
        self.notify_all(self.DID_SHUTDOWN)

    def run(self):
        self.notify_all(self.WILL_RUN)
        self.start()
        self.loop_thread.start()
        self.loop_thread.join()
        for address, session in self.sessions:
            session.join()
        self.stop()
        self.notify_all(self.DID_RUN)

    def on_send_success(self, session, message):
        print('*** SEND [{timestamp}] ***\n[{address}] <= "{message}"\n***  END [{timestamp}] ***\n'.format(
            timestamp=datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
            address=session.address,
            message=message))

    def on_recv_success(self, session, buffersize, message):
        print('*** RECV [{timestamp}] ***\n[{address}] => "{message}"\n***  END [{timestamp}] ***\n'.format(
            timestamp=datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
            address=session.address,
            message=message))
