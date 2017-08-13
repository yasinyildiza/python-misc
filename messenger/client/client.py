#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os, socket, threading, time, datetime, json
from Tkinter import *

BUFFER_SIZE = 1024
rowCounter = 0
root = None
client = None
sender = None

class ScrollBar(Frame):
    def __init__(self, root):

        Frame.__init__(self, root)
        self.canvas = Canvas(root, borderwidth=0, background="#ffffff")
        self.frame = Frame(self.canvas, background="#ffffff")
        self.vsb = Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vsb.set)
        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.create_window((4,4), window=self.frame, anchor="nw", tags="self.frame")
        self.frame.bind("<Configure>", self.OnFrameConfigure)
    def OnFrameConfigure(self, event):
        '''Reset the scroll region to encompass the inner frame'''
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    def onMouseWheel(self, event):
        self.canvas.yview_scroll(-1*(event.delta/120), "units")

class TCPsender(threading.Thread):
    def __init__(self, client, root):
        global rowCounter
        threading.Thread.__init__(self)
        self.root = root
        self.client = client
        self.v = StringVar()
        self.entry = Entry(self.root, textvariable=self.v)
        self.entry.grid(row=rowCounter, column=0)
        #rowCounter += 1
        self.button = Button(self.root, text="Send", command=self.send)
        self.button.grid(row=rowCounter, column=1, columnspan=2)
        rowCounter += 1
    def enterPressed(self, event):
        self.send()
    def send(self):
        global rowCounter
        if self.client.is_connected:
            message = self.v.get()
            if message == "":
                return
            self.client.send(message)
            messageTime = datetime.datetime.now().strftime("%Y:%m:%d:%H:%M:%S.%f")
            label = Label(self.root, text=message, font=("Helvetica", 12), fg="black", anchor=W, justify=RIGHT, wraplength=100)
            label.grid(row=rowCounter, column=1)
            rowCounter += 1
            label = Label(self.root, text=messageTime, font=("Helvetica", 6), fg="gray", anchor=W, justify=RIGHT, wraplength=100)
            label.grid(row=rowCounter, column=1)
            rowCounter += 1
            self.v.set("")
    def run(self):
        pass

class TCPclient(threading.Thread):
    def __init__(self, ip, port, root):
        threading.Thread.__init__(self)
        self.root = root
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.is_connected = False
        self.connect()
    def connect(self):
        if self.is_connected:
            return
        self.socket.connect((self.ip, self.port))
        self.is_connected = True
        self.start()
    def receive(self, size):
        if self.is_connected:
            return self.socket.recv(size)
        return ""
    def send(self, message):
        if self.is_connected:
            self.socket.send(message.encode("utf-8"))
    def close(self):
        self.socket.close()
    def run(self):
        global rowCounter
        while True:
            if self.is_connected:
                message = ""
                try:
                    message = self.receive(BUFFER_SIZE)
                except:
                    self.is_connected = False
                if len(message) > 0:
                    if message == "exit":
                        break
                    messageDict = json.loads(message, encoding='utf-8')
                    label = Label(self.root, text=messageDict["sender"], font=("Helvetica", 8), fg="blue", anchor=E, justify=LEFT, wraplength=100)
                    label.grid(row=rowCounter, column=0)
                    rowCounter += 1
                    label = Label(self.root, text=messageDict["content"], font=("Helvetica", 12), fg="black", anchor=E, justify=LEFT, wraplength=100)
                    label.grid(row=rowCounter, column=0)
                    rowCounter += 1
                    label = Label(self.root, text=messageDict["time"], font=("Helvetica", 6), fg="gray", anchor=E, justify=LEFT, wraplength=100)
                    label.grid(row=rowCounter, column=0)
                    rowCounter += 1
                else:
                    self.is_connected = False
                    break
            else:
                break


def handleExit():
    global root
    global client
    global sender
    client.send("exit")
    time.sleep(1)
    #client.close()
    root.destroy()

root = Tk()
root.geometry("300x500")
root.protocol("WM_DELETE_WINDOW", handleExit)

scrollbar = ScrollBar(root)
scrollbar.pack(side="top", fill="both", expand=True)

#root.bind_all("<MouseWheel>", scrollbar.onMouseWheel)

TCP_IP = "localhost"
TCP_PORT = 4000

conf_file = "client.conf" 

if os.path.exists(conf_file):
    ftr = open(conf_file, "r")
    info = ftr.readline()
    ftr.close()
    
    splitted_info = info.split(":")

    TCP_IP = splitted_info[0]
    TCP_PORT = int(splitted_info[1], 10)
else:
    sys.exit(conf_file + " does not exist")

root.wm_title("Client " + TCP_IP + ":" + str(TCP_PORT))
client = TCPclient(TCP_IP, TCP_PORT, scrollbar.frame)
sender = TCPsender(client, scrollbar.frame)
root.bind("<Return>", sender.enterPressed)

root.mainloop()
