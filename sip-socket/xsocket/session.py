import socket
import threading
import time

import notifier

class Session(notifier.Notifier):

    ON_SENDING      = 'on_sending'
    ON_SEND_SUCCESS = 'on_send_success'
    ON_SEND_FAILURE = 'on_send_failure'

    ON_RECVING      = 'on_recving'
    ON_RECV_SUCCESS = 'on_recv_success'
    ON_RECV_FAILURE = 'on_recv_failure'

    ON_CLOSING       = 'on_closing'
    ON_CLOSE_SUCCESS = 'on_close_success'
    ON_CLOSE_FAILURE = 'on_close_failure'

    def __init__(self, connection, address):
        notifier.Notifier.__init__(self)

        self.connection  = connection
        self.address     = address

        self.loop_message     = 'I am the server'
        self.loop_buffersize  = 1024
        self.loop_period_send = 5
        self.loop_period_recv = 3

        self.enable_send_loop = False
        self.enable_recv_loop = False

        self.send_thread = threading.Thread(target=self.send_loop)
        self.recv_thread = threading.Thread(target=self.recv_loop)

    def sendx(self, message):
        raise Exception('Session::sendx method must be implemented by child class')

    def send(self, message):
        self.notify_all(self.ON_SENDING, message)

        try:
            self.sendx(message)
        except socket.error as error:
            self.notify_all(self.ON_SEND_FAILURE, message, error)
        else:
            self.notify_all(self.ON_SEND_SUCCESS, message)

    def send_loop(self):
        while True:
            try:
                self.send(self.loop_message)
            except Exception as error:
                print('send_loop error: {error}'.format(error=error))
                break
            time.sleep(self.loop_period_send)

    def recvx(self, buffersize):
        raise Exception('Session::recvx method must be implemented by child class')

    def recv(self, buffersize):
        self.notify_all(self.ON_RECVING, buffersize)

        try:
            message = self.recvx(buffersize)
        except socket.error as error:
            self.notify_all(self.ON_RECV_FAILURE, buffersize, error)
        else:
            self.notify_all(self.ON_RECV_SUCCESS, buffersize, message)

    def recv_loop(self):
        while True:
            try:
                self.recv(self.loop_buffersize)
            except Exception as error:
                print('recv_loop error: {error}'.format(error=error))
                break
            time.sleep(self.loop_period_recv)

    def closex(self):
        raise Exception('Session::closex method must be implemented by child class')

    def close(self):
        self.notify_all(self.ON_CLOSING)

        try:
            self.closex()
        except socket.error as error:
            self.notify_all(self.ON_CLOSE_FAILURE, error)
            raise
        else:
            self.notify_all(self.ON_CLOSE_SUCCESS)

    def start(self):
        if self.enable_send_loop:
            self.send_thread.start()

        if self.enable_recv_loop:
            self.recv_thread.start()

    def join(self):
        if self.enable_send_loop:
            self.send_thread.join()
        if self.enable_recv_loop:
            self.recv_thread.join()

        self.close()
