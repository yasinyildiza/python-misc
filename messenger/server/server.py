#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, socket, threading, time, datetime, json
from Tkinter import *

BUFFER_SIZE = 1024
server = None
root = None

class SessionMessageSender(threading.Thread):
    def __init__(self, conn, addr, root):
        threading.Thread.__init__(self)
        self.root = root
        self.conn = conn
        self.addr = addr
        self.is_connected = True
    def send(self, message):
        if self.is_connected and message != "":
            self.conn.send(message)

class SessionMessageReceiver(threading.Thread):
    def __init__(self, conn, addr, root):
        threading.Thread.__init__(self)
        self.root = root
        self.conn = conn
        self.addr = addr
        self.address = self.addr[0] + ":" + str(self.addr[1])
        self.is_connected = True
        self.start()
    def receive(self, size):
        if self.is_connected:
            return self.conn.recv(size).decode("utf-8")
        return ""
    def run(self):
        global server
        while True:
            if self.is_connected:
                message = ""
                try:
                    message = self.receive(BUFFER_SIZE)
                except:
                    self.is_connected = False
                    return
                if len(message) > 0:
                    if message == "exit":
                        for session in server.sessions:
                            if session.receiver == self:
                                session.sender.send("exit")
                                connection = self.address + " disconnected"
                                label = Label(self.root, text=connection)
                                label.pack()
                                break
                        break
                    messageDict = {}
                    messageDict["sender"] = self.address
                    messageDict["content"] = message
                    messageDict["time"] = datetime.datetime.now().strftime("%Y:%m:%d:%H:%M:%S.%f")
                    messageText = json.dumps(messageDict).encode('utf8')
                    label = Label(self.root, text=messageText)
                    label.pack()
                    for session in server.sessions:
                        if session.receiver != self:
                            session.sender.send(messageText)
                else:
                    self.is_connected = False
                    break
            else:
                break

class ServerSession(threading.Thread):
    def __init__(self, conn, addr, root):
        threading.Thread.__init__(self)
        self.root = root
        self.conn = conn
        self.addr = addr
        self.is_connected = True
        self.sender = SessionMessageSender(self.conn, self.addr, self.root)
        self.receiver = SessionMessageReceiver(self.conn, self.addr, self.root)
    def disconnect(self):
        self.sender.send("exit")
        connection = self.receiver.address + " disconnected"
        label = Label(self.root, text=connection)
        label.pack()
        self.is_connected = False
        self.sender.is_connected = False
        self.receiver.is_connected = False
    def close(self):
        self.conn.close()

class TCPserver(threading.Thread):
    def __init__(self, ip, port, root):
        threading.Thread.__init__(self)
        self.root = root
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.ip, self.port))
        self.socket.listen(1)
        self.sessions = []
        self.start()
    def accept(self):
    	conn, addr = self.socket.accept()
    	session = ServerSession(conn, addr, self.root)
    	self.sessions.append(session)
    	connection = addr[0] + ":" + str(addr[1]) + " connected"
    	label = Label(self.root, text=connection)
    	label.pack()
    def run(self):
        while True:
            self.accept();
    def close(self):
        for session in self.sessions:
            session.close()

def handleExit():
    global root
    global server
    root.destroy()
    server.close()

root = Tk()
root.protocol("WM_DELETE_WINDOW", handleExit)


TCP_IP = '0.0.0.0'
TCP_PORT = 4000

conf_file = "server.conf"
if os.path.exists(conf_file):
    ftr = open(conf_file, "r")
    port = ftr.read(4)
    ftr.close()
    TCP_PORT = int(port, 10)
else:
    sys.exit(conf_file + " does not exist")

root.wm_title("Server " + str(TCP_PORT))
server = TCPserver(TCP_IP, TCP_PORT, root)

root.mainloop()
