import constants
import server
import session

class Session(session.Session):

    def __init__(self, connection, address):
        session.Session.__init__(self, connection, address)

    def sendx(self, message):
        self.connection.sendto(message, self.address)

    def recvx(self, buffersize):
        message, address = self.connection.recvfrom(buffersize)
        return message

    def closex(self):
        pass

class Server(server.Server):

    def __init__(self, port, buffersize, sendloop, recvloop):
        server.Server.__init__(self, self.UDP, port, buffersize, sendloop, recvloop)

    def startx(self):
        pass

    def acceptx(self):
        message, address = self.socket.recvfrom(self.buffersize)
        if address in self.sessions:
            session = self.sessions[address]
        else:
            session = Session(self.socket, address)

        session.notify_all(session.ON_RECV_SUCCESS, self.buffersize, message)
        self.on_recv_success(session, self.buffersize, message)
        return session

    def stopx(self):
        pass

    def shutdownx(self):
        pass
