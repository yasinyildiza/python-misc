import client
import constants

class Client(client.Client):

    def __init__(self, ip, port, timeout, sendloop, recvloop, sendrecvloop, sslversion, maximum_trial_count):
        client.Client.__init__(self, self.UDP, ip, port, timeout, sendloop, recvloop, sendrecvloop, sslversion, maximum_trial_count)

    def connectx(self):
        pass

    def sendx(self, message):
        self.socket.sendto(message, self.address)

    def recvx(self, buffersize):
        message = self.socket.recvfrom(buffersize)
        return message
