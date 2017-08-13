import datetime
import Queue
import sys
import threading
import time

global_input_buffer = Queue.Queue()
global_output_buffer = Queue.Queue()

DEBUG = 'debug' in sys.argv

def get_timestamp():
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')

def log(action, obj):
    if DEBUG:
        timestamp = get_timestamp()
        print('[{timestamp}] {action}: {obj}'.format(timestamp=timestamp, action=action, obj=obj))

def register(request):
    log('register', request)
    obj = (process, request)
    global_input_buffer.put(obj)

def process(request):
    log('process', request)
    #time.sleep(100/request)
    time.sleep(1)
    return request

def send(response):
    log('send', response)

class Looper(threading.Thread):

    def __init__(self, index):
        threading.Thread.__init__(self)

        self.index = index

        self.name = self.__class__.__name__.lower() + '_' + str(self.index)

        self.debug = self.name in sys.argv or DEBUG

        print('{name} [debug]: {debug}'.format(name=self.name, debug=self.debug))

    def log(self, text):
        if self.debug:
            print(text)

    def loop_single(self):
        raise Exception('Looper::loop_single method must be implemented by child class')

    def run(self):
        while True:
            self.loop_single()
            time.sleep(1)

class Sender(Looper):

    def __init__(self, index):
        Looper.__init__(self, index)

    def loop_single(self):
        if not global_output_buffer.empty():
            sender, response = global_output_buffer.get()
            sender(response)

class Processor(Looper):

    def __init__(self, index):
        Looper.__init__(self, index)

    def loop_single(self):
        if not global_input_buffer.empty():
            handler, request = global_input_buffer.get()
            response = handler(request)
            obj = (send, response)
            global_output_buffer.put(obj)

class Registerer(Looper):

    def __init__(self, index):
        Looper.__init__(self, index)

        self.counter = 1

    def loop_single(self):
        register(self.counter)
        self.counter += 1

class Application(object):

    def __init__(self, processor_counter=1, sender_counter=1):
        self.registerer = Registerer(0)

        self.processors = []
        for i in range(processor_counter):
            self.processors.append(Processor(i))

        self.senders = []
        for i in range(sender_counter):
            self.senders.append(Sender(i))

    def run(self):
        self.registerer.start()

        for processor in self.processors:
            processor.start()

        for sender in self.senders:
            sender.start()

        self.registerer.join()

        for processor in self.processors:
            processor.join()

        for sender in self.senders:
            sender.join()

def main():
    Application(processor_counter=4).run()

if __name__ == '__main__':
    main()
