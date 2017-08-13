import socket

import constants
import server
import session

class Session(session.Session):

    def __init__(self, connection, address):
        session.Session.__init__(self, connection, address)

    def sendx(self, message):
        self.connection.sendall(message)

    def recvx(self, buffersize):
        message = self.connection.recv(buffersize)
        return message

    def closex(self):
        self.connection.close()

class Server(server.Server):

    def __init__(self, port, buffersize, sendloop, recvloop):
        server.Server.__init__(self, self.TCP, port, buffersize, sendloop, recvloop)

    def startx(self):
        self.socket.listen(1)

    def acceptx(self):
        connection, address = self.socket.accept()
        session = Session(connection, address)
        return session
