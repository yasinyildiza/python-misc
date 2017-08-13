import client
import constants

class Client(client.Client):

    def __init__(self, ip, port, timeout, sendloop, recvloop, sendrecvloop, sslversion, maximum_trial_count):
        client.Client.__init__(self, self.TCP, ip, port, timeout, sendloop, recvloop, sendrecvloop, sslversion, maximum_trial_count)

    def connectx(self):
        self.socket.connect(self.address)

    def sendx(self, message):
        self.socket.sendall(message)

    def recvx(self, buffersize):
        message = self.socket.recv(buffersize)
        return message
